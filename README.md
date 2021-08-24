# emr-cost

EMR cost utility.

This utility is greatly inspired by https://github.com/memosstilvi/emr-cost-calculator and some of its forks, particularly the `EMRPriceMeta` class was adapted from their previous work.

Auth relays local AWS context, such as through the official [AWS CLI](https://aws.amazon.com/cli/) and its established local configurations.

## Install

```shell
% pip install git+https://github.com/EQWorks/emr-cost.git#egg=emr-cost
% # or
% python -m pip install git+https://github.com/EQWorks/emr-cost.git#egg=emr-cost
```

Note: you may need to switch to `pip3` or `python3` depending on your OS. You can also use `pipenv` (or other similar tools) in place of the above `pip` example.

## CLI

You can get help by running:

```shell
% emr-cost --help
```

### CLI Examples

To get the costs of EMR clusters that ran (`'ClusterStates': ['TERMINATED']`) in the current month so far, and pretty-print the output to shell/console:

```shell
% emr-cost
  2%|█▎                                                          | 18/795 [01:48<1:05:46,  5.08s/it]

# output here after done, that would look like
[{...},
...
 {'ClusterId': 'total',
  'CreationDateTime': None,
  'EbsBlockDevices': None,
  'EndDateTime': None,
  'InstanceGroupType': None,
  'InstanceType': None,
  'Market': None,
  'Name': None,
  'cost_ebs': 93,
  'cost_ec2': 321,
  'cost_emr': 96}]
```


To get the costs of EMR clusters that ran in month of July, 2021, and output to a CSV file (`2021-07.csv`):

```shell
% emr-cost --month 2021-07-01 --output 2021-07.csv
 11%|██████▍                                                   | 134/1206 [06:35<1:06:47,  3.74s/it]
```

To get the cost of a specific EMR cluster by `ClusterId`:

```shell
% emr-cost --cluster_id <REDACTED>
100%|█████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00,  1.65it/s]
[{'ClusterId': '<REDACTED>',
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
