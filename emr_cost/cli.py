import csv
import json
from datetime import datetime, timedelta
from pprint import pprint

from tqdm import tqdm
import click

from emr_cost import list_clusters, get_instances, calculate_cost, EMRPriceMeta, __version__


# adapted from: https://stackoverflow.com/a/13565185/158111
def month_range(date):
    # this will never fail
    # get close to the end of the month for any day, and add 4 days 'over'
    next_month = date.replace(day=28) + timedelta(days=4)
    # subtract the number of remaining 'overage' days to get last day of current month, or said programattically said, the previous day of the first of next month
    last_day = next_month - timedelta(days=next_month.day)
    return {
        'CreatedAfter': datetime.combine(last_day.replace(day=1), datetime.min.time()),
        'CreatedBefore': datetime.combine(last_day, datetime.max.time()),
    }


@click.command()
@click.option('--cluster_id', help='Get the cost of a specific EMR cluster by ClusterId')
@click.option('--batch', type=click.File('r'), help='Batch input file, one ClusterId per-line')
@click.option('--output', help='Output file. CSV if the output file ends with .csv, otherwise JSON')
@click.option('--month', help='Get the month of the given date in the format of 2021-08-24')
@click.option('--version', is_flag=True)
def cli(cluster_id, batch, output, month, version):
    if version:
        return click.echo(__version__)

    price_meta = EMRPriceMeta()

    cost_fields = ['cost_ec2', 'cost_emr', 'cost_ebs']
    fieldnames = [
        'ClusterId',
        'Name',
        'InstanceGroupType',
        'EbsBlockDevices',
        'CreationDateTime',
        'EndDateTime',
        'InstanceType',
        'Market',
        *cost_fields,
    ]
    total = {f: None for f in fieldnames}
    total['ClusterId'] = 'total'

    costs = []
    clusters = []
    if cluster_id:
        clusters = [cluster_id]
    elif batch:
        clusters = [c.strip() for c in batch.readlines()]
    elif month:
        range = month_range(datetime.strptime(month, '%Y-%m-%d'))
        clusters = list_clusters(**range)
    else:
        clusters = list_clusters()

    for c in tqdm(clusters, ncols=100):
        for i in get_instances(c):
            cost = calculate_cost(i, price_meta)
            costs.append(cost)
            for f in cost_fields:
                total[f] = (total[f] or 0) + cost[f]

    costs.append(total)

    if output:
        with open(output, 'w', encoding='utf8') as out:
            if output.endswith('.csv'):
                csv_writer = csv.DictWriter(out, fieldnames=fieldnames)
                csv_writer.writeheader()
                for cost in costs:
                    csv_writer.writerow(cost)
            else:
                json.dump(costs, out, default=str)
    else:
        pprint(costs)
