import json
import time
import random
import sys
import os
from datetime import datetime

import requests
import boto3
from botocore.exceptions import ClientError


__version__ = '0.1.0'

emr = boto3.client('emr')


def backoff(n):
    return (2 ** n) + (random.randint(0, 1000) / 1000)



def list_clusters(
    CreatedAfter: datetime = None,
    CreatedBefore: datetime = None,
    ClusterStates: list = ['TERMINATED'],
):
    if not CreatedAfter and not CreatedBefore:
        CreatedAfter = datetime.today().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    kwargs = {'CreatedAfter': CreatedAfter, 'ClusterStates': ClusterStates}
    if CreatedBefore:
        kwargs['CreatedBefore'] = CreatedBefore

    clusters = []
    pages = emr.get_paginator('list_clusters').paginate(**kwargs)
    for page in pages:
        for item in page['Clusters']:
            clusters.append(item['Id'])

    return clusters


# TODO: pagination support?
def _list_groups(ClusterId: str, retry: int = 0):
    try:
        r = emr.list_instance_groups(ClusterId=ClusterId)
        return r.get('InstanceGroups', [])
    except ClientError as e:
        if e.response['Error']['Code'] == 'ThrottlingException' and retry <= 4:
            time.sleep(backoff(retry))
            return _list_groups(ClusterId, retry=retry + 1)
        raise

# TODO: pagination support?
def _list_fleets(ClusterId: str, retry: int = 0):
    try:
        r = emr.list_instance_fleets(ClusterId=ClusterId)
        return r.get('InstanceFleets', [])
    except ClientError as e:
        if e.response['Error']['Code'] == 'ThrottlingException' and retry <= 4:
            time.sleep(backoff(retry))
            return _list_fleets(ClusterId, retry=retry + 1)
        raise


# TODO: pagination support?
def _list_instances(retry: int = 0, **kwargs):
    try:
        r = emr.list_instances(**kwargs)
        return r.get('Instances')
    except ClientError as e:
        if e.response['Error']['Code'] == 'ThrottlingException' and retry <= 4:
            time.sleep(backoff(retry))
            return _list_instances(retry=retry + 1, **kwargs)
        raise


def get_instances(ClusterId: str):
    cluster = emr.describe_cluster(ClusterId=ClusterId)
    if cluster.get('ResponseMetadata', {}).get('HTTPStatusCode') != 200:
        raise Exception(f'Unable to describe EMR cluster {ClusterId}')

    cluster = cluster.get('Cluster', {})
    Name = cluster.get('Name')
    coll_type = cluster.get('InstanceCollectionType')
    instances = []
    # TODO: revise this mess
    if coll_type == 'INSTANCE_GROUP':
        for g in _list_groups(ClusterId):
            for i in _list_instances(ClusterId=ClusterId, InstanceGroupId=g['Id']):
                instances.append({
                    'ClusterId': ClusterId,
                    'Name': Name,
                    'InstanceGroupType': g['InstanceGroupType'],
                    'EbsBlockDevices': g['EbsBlockDevices'],
                    'CreationDateTime': i['Status']['Timeline']['CreationDateTime'],
                    'EndDateTime': i['Status']['Timeline']['EndDateTime'],
                    'InstanceType': i['InstanceType'],
                    'Market': i['Market'],
                })
    elif coll_type == 'INSTANCE_FLEET':
        for f in _list_fleets(ClusterId):
            for i in _list_instances(ClusterId=ClusterId, InstanceFleetId=f['Id']):
                instances.append({
                    'ClusterId': ClusterId,
                    'Name': Name,
                    'InstanceGroupType': f['InstanceFleetType'],
                    'EbsBlockDevices': f['InstanceTypeSpecifications'][0]['EbsBlockDevices'],
                    'CreationDateTime': i['Status']['Timeline']['CreationDateTime'],
                    'EndDateTime': i['Status']['Timeline']['EndDateTime'],
                    'InstanceType': i['InstanceType'],
                    'Market': i['Market'],
                })
    else:
        raise Exception(f'Unable to get collection type of cluster {ClusterId}\n{json.dumps(cluster, indent=2, default=str)}')

    return instances


# TODO: spot instance pricing support (right now all based on ON_DEMAND)
def calculate_cost(instance: dict, price_meta):
    hours = ((instance['EndDateTime'] - instance['CreationDateTime']).total_seconds() / 3600)
    # EC2 cost
    ec2 = price_meta.ec2_hourly(instance['InstanceType']) * hours
    # EMR cost
    emr = price_meta.emr_hourly(instance['InstanceType']) * hours
    # EBS cost
    gbs = 0
    for device in instance['EbsBlockDevices']:
        gbs += device['VolumeSpecification']['SizeInGB']
    ebs = gbs * 0.1 * hours / (24 * 30)

    return {
        **instance,
        'EbsBlockDevices': gbs,  # override list of devices to sum of GBs
        'cost_ec2': ec2,
        'cost_emr': emr,
        'cost_ebs': ebs,
    }


# adapted from https://github.com/mauropelucchi/aws-emr-cost-calculator
# add caching of index and regional cost meta JSON from AWS
class EMRPriceMeta:
    BASE_URL = 'https://pricing.us-east-1.amazonaws.com'
    CACHE_DIR = os.path.expanduser('~/.emr-cost')

    def _get_index(self):
        cache = f'{self.CACHE_DIR}/index.json'
        try:
            with open(cache) as f:
                self._index = json.load(f)
                self._index['offers']  # weak-test on validity of the cache file
        except:
            self._index = requests.get(f'{self.BASE_URL}/offers/v1.0/aws/index.json').json()
            with open(cache, 'w') as f:
                json.dump(self._index, f, default=str)

    def _get_regional_emr(self):
        cache = f'{self.CACHE_DIR}/{self._region}_emr.json'
        try:
            with open(cache) as f:
                self._emr_pricing = json.load(f)
                self._emr_pricing['products']  # weak-test on validity of the cache file
        except:
            region = requests.get(self.BASE_URL + self._index['offers']['ElasticMapReduce']['currentRegionIndexUrl']).json()
            regional_emr = self.BASE_URL + region['regions'][self._region]['currentVersionUrl']
            self._emr_pricing = requests.get(regional_emr).json()
            with open(cache, 'w') as f:
                json.dump(self._emr_pricing, f, default=str)

    def _get_regional_ec2(self):
        cache = f'{self.CACHE_DIR}/{self._region}_ec2.json'
        try:
            with open(cache) as f:
                self._ec2_pricing = json.load(f)
                self._ec2_pricing['products']  # weak-test on validity of the cache file
        except:
            region = requests.get( self.BASE_URL + self._index['offers']['AmazonEC2']['currentRegionIndexUrl']).json()
            regional_ec2 = self.BASE_URL + region['regions'][self._region]['currentVersionUrl']
            self._ec2_pricing = requests.get(regional_ec2).json()
            with open(cache, 'w') as f:
                json.dump(self._ec2_pricing, f, default=str)


    def __init__(self, region: str = None):
        os.makedirs(self.CACHE_DIR, exist_ok=True)

        if region is None:
            my_session = boto3.session.Session()
            region = my_session.region_name

        self._region = region
        self._get_index()
        self._get_regional_emr()
        self._get_regional_ec2()

        sku_to_instance_type = {}
        for sku in self._emr_pricing['products']:
            if (('softwareType' in self._emr_pricing['products'][sku]['attributes'].keys()) and
               (self._emr_pricing['products'][sku]['attributes']['softwareType'] == 'EMR')):
                sku_to_instance_type[sku] = self._emr_pricing['products'][sku]['attributes']['instanceType']

        self.emr_prices = {}
        for sku in sku_to_instance_type.keys():
            instance_type = sku_to_instance_type.get(sku)
            sku_info = self._emr_pricing['terms']['OnDemand'][sku]
            if len(sku_info) > 1:
                print('[ERROR] More than one SKU for {}'.format(sku_info), file=sys.stderr)
                sys.exit(1)
            _, sku_info_value = sku_info.popitem()
            price_dimensions = sku_info_value['priceDimensions']
            if len(sku_info) > 1:
                print('[ERROR] More than m dimension for {}'.format(price_dimensions), file=sys.stderr)
                sys.exit(1)
            _, price_dimensions_value = price_dimensions.popitem()
            price = float(price_dimensions_value['pricePerUnit']['USD'])
            self.emr_prices[instance_type] = price

        ec2_sku_to_instance_type = {}
        for sku in self._ec2_pricing['products']:
            try:
                attr = self._ec2_pricing['products'][sku]['attributes']
                if attr['tenancy'] == 'Shared' and attr['operatingSystem'] == 'Linux' and attr['operation'] == 'RunInstances' and attr['capacitystatus'] == 'Used':
                    ec2_sku_to_instance_type[sku] = attr['instanceType']
            except KeyError:
                pass

        self.ec2_prices = {}
        for sku in ec2_sku_to_instance_type.keys():
            instance_type = ec2_sku_to_instance_type.get(sku)
            sku_info = self._ec2_pricing['terms']['OnDemand'][sku]
            if len(sku_info) > 1:
                print('[ERROR] More than one SKU for {}'.format(sku_info), file=sys.stderr)
                sys.exit(1)
            _, sku_info_value = sku_info.popitem()
            price_dimensions = sku_info_value['priceDimensions']
            if len(sku_info) > 1:
                print('[ERROR] More than price dimension for {}'.format(price_dimensions), file=sys.stderr)
                sys.exit(1)
            _, price_dimensions_value = price_dimensions.popitem()
            price = float(price_dimensions_value['pricePerUnit']['USD'])
            if instance_type in self.ec2_prices:
                print('[ERROR] Instance price for {} already added'.format(instance_type), file=sys.stderr)
                sys.exit(1)

            self.ec2_prices[instance_type] = price

    def emr_hourly(self, instance_type):
        return self.emr_prices[instance_type]

    def ec2_hourly(self, instance_type):
        return self.ec2_prices[instance_type]
