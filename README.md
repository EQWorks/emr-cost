# emr-cost

EMR cost utility.

This utility is greatly inspired by https://github.com/memosstilvi/emr-cost-calculator and some of its forks, particularly the `EMRPriceMeta` class was adapted from their previous work.

Auth relays local AWS context, such as through the official [AWS CLI](https://aws.amazon.com/cli/) and its established local configurations.

## Install

```shell
% pip install git+https://github.com/EQWorks/emr-cost.git#egg=emr-cost
```

## CLI

You can get help by running:

```shell
% emr-cost --help
```

### CLI Examples

To get the costs of EMR clusters that ran (`'ClusterStates': ['TERMINATED']`) in month of July, 2021, and output to a CSV file (`2021-07.csv`):

```shell
% % emr-cost --month 2021-07-01 --output 2021-07.csv
 11%|██████▍                                                   | 134/1206 [06:35<1:06:47,  3.74s/it]
```

To get the cost of a specific EMR cluster by `ClusterId`:

```shell
% emr-cost --cluster_id j-360S2UNZ64OU7
100%|█████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00,  1.65it/s]
[{'ClusterId': 'j-360S2UNZ64OU7',
  'CreationDateTime': datetime.datetime(2021, 8, 11, 10, 1, 33, 557000, tzinfo=tzlocal()),
  'EbsBlockDevices': 500,
  'EndDateTime': datetime.datetime(2021, 8, 11, 15, 29, 0, 448000, tzinfo=tzlocal()),
  'InstanceGroupType': 'CORE',
  'InstanceType': 'r4.xlarge',
  'Market': 'ON_DEMAND',
  'Name': '<REDACTED>',
  'cost_ebs': 0.3789909529320988,
  'cost_ec2': 1.4516869461111113,
  'cost_emr': 0.3656504713888889},
...
 {'ClusterId': 'total',
  'CreationDateTime': None,
  'EbsBlockDevices': None,
  'EndDateTime': None,
  'InstanceGroupType': None,
  'InstanceType': None,
  'Market': None,
  'Name': None,
  'cost_ebs': 2.273945717592593,
  'cost_ec2': 8.349928675000001,
  'cost_emr': 2.1557005402777776}]
```

To get the costs of a batch of multiple clusters from text file `third.txt` (one `ClusterId` per-line), and output to a JSON file (`third.json`):

```shell
% emr-cost --batch third.txt --output third.json
 16%|██████████▎                                                     | 5/31 [00:07<00:22,  1.18it/s]
```

## Library

WIP. See the [libary](emr_cost/__init__.py) and its [CLI application](emr_cost/cli.py) for now.
