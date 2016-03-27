#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: ec2_snapshot_facts
short_description: Gather facts about ec2 volume snapshots in AWS
description:
    - Gather facts about ec2 volume snapshots in AWS
version_added: "2.0"
author: "Rob White (@wimnat)"
options:
  snapshot_ids:
    description:
      - A list of one or more snapshot IDs to return
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. See U(http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeSnapshots.html) for possible filters.
    required: false
    default: null
notes:
  - By default, the module will return all snapshots, including public ones. To limit results to snapshots owned by the account use the filter 'owner-id'.

extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather facts about all snapshots, including public ones
- ec2_snapshot_facts:

# Gather facts about all snapshots owned by the account 0123456789
- ec2_snapshot_facts:
    filters:
      owner-id: 0123456789

# Gather facts about a particular snapshot using ID
- ec2_snapshot_facts:
    filters:
      snapshot-id: snap-00112233

# Gather facts about any snapshot with a tag key Name and value Example
- ec2_snapshot_facts:
    filters:
      "tag:Name": Example

# Gather facts about any snapshot with an error status
- ec2_snapshot_facts:
    filters:
      status: error

'''

RETURN = '''
snapshot_id:
    description: The ID of the snapshot. Each snapshot receives a unique identifier when it is created.
    type: string
    sample: snap-01234567
volume_id:
    description: The ID of the volume that was used to create the snapshot.
    type: string
    sample: vol-01234567
state:
    description: The snapshot state (completed, pending or error).
    type: string
    sample: completed
state_message:
    description: Encrypted Amazon EBS snapshots are copied asynchronously. If a snapshot copy operation fails (for example, if the proper AWS Key Management Service (AWS KMS) permissions are not obtained) this field displays error state details to help you diagnose why the error occurred.
    type: string
    sample:
start_time:
    description: The time stamp when the snapshot was initiated.
    type: datetime
    sample: 2015-02-12T02:14:02+00:00
progress:
    description: The progress of the snapshot, as a percentage.
    type: percentage
    sample: 100%
owner_id:
    description: The AWS account ID of the EBS snapshot owner.
    type: string
    sample: 099720109477
description:
    description: The description for the snapshot.
    type: string
    sample: My important backup
volume_size:
    description: The description for the snapshot.
    type: string
    sample: My important backup
owner_alias:
    description: The description for the snapshot.
    type: string
    sample: My important backup
tags:
    description: The description for the snapshot.
    type: string
    sample: My important backup
encrypted:
    description: The description for the snapshot.
    type: string
    sample: My important backup
kms_key_id:
    description: The description for the snapshot.
    type: string
    sample: My important backup
data_encryption_key_id:
    description: The description for the snapshot.
    type: string
    sample: My important backup

'''

try:
    import boto3
    import botocore.exceptions
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def camel_dict_to_snake_dict(camel_dict):

    def camel_to_snake(name):

        import re

        first_cap_re = re.compile('(.)([A-Z][a-z]+)')
        all_cap_re = re.compile('([a-z0-9])([A-Z])')
        s1 = first_cap_re.sub(r'\1_\2', name)

        return all_cap_re.sub(r'\1_\2', s1).lower()

    snake_dict = {}
    for k, v in camel_dict.iteritems():
        if isinstance(v, dict):
            v = camel_dict_to_snake_dict(v)
        snake_dict[camel_to_snake(k)] = v

    return snake_dict


def make_filter_list(filters_dict):

    filter_list = []

    for k,v in filters_dict.iteritems():
        filter_dict = {'Name': k}
        if isinstance(v, basestring):
            filter_dict['Values'] = [ v ]
        else:
            filter_dict['Values'] = v

        filter_list.append(filter_dict)

    return filter_list


def list_ec2_snapshots(connection, module):

    snapshot_ids = module.params.get("snapshot_ids")
    owner_ids = module.params.get("owner_ids")
    restorable_by_user_ids = module.params.get("restorable_by_user_ids")
    filters = make_filter_list(module.params.get("filters"))

    snapshots = connection.describe_snapshots(SnapshotIds=snapshot_ids, OwnerIds=owner_ids, RestorableByUserIds=restorable_by_user_ids, Filters=filters)

    snaked_snapshots = []
    for snapshot in snapshots['Snapshots']:
        snaked_snapshots.append(camel_dict_to_snake_dict(snapshot))

    module.exit_json(snapshots=snaked_snapshots)


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            snapshot_ids = dict(default=[], type='list'),
            owner_ids = dict(default=[], type='list'),
            restorable_by_user_ids = dict(default=[], type='list'),
            filters = dict(default={}, type='dict')
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    connection = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_params)

    list_ec2_snapshots(connection, module)

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
