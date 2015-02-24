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

DOCUMENTATION = """
---
module: elastictranscoder
short_description: Create or delete AWS Elastic Transcoder Pipelines
description:
  - Can create or delete AWS Elastic Transcoder Pipelines
version_added: "1.8"
author: Rob White
options:
  state:
    description:
      - register or deregister the instance
    required: true
    choices: ['present', 'absent']
  name:
    description:
      - Unique (recommended) name for pipeline
    required: true
  input_bucket:
    description:
      - The Amazon S3 bucket in which you saved the media files that you want to transcode
    required: true
  output_bucket:
    description:
      - The Amazon S3 bucket in which you want Elastic Transcoder to save the transcoded files
    required: true
  notifications:
    description:
      - The Amazon Simple Notification Service (Amazon SNS) topic that you want to notify to report job status. You can specify a topic for Progress, Complete, Warning and Error status as a list
    required: false
  role:
    description:
      - The IAM Amazon Resource Name (ARN) for the role that you want Elastic Transcoder to use to create the pipeline
    required: false
extends_documentation_fragment: aws
"""

EXAMPLES = '''
- elastictranscoder:
    name: production
    input_bucket: input_bucket.in.s3
    output_bucket: output_bucket.in.s3
    notifications:
      progress: something1
      complete: something2
      warning: something3
      error: something4
    role: arn:aws:iam::0123456789:role/elastictranscoder

'''

import sys
import time

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

try:
    import boto.elastictranscoder
    from boto.exception import BotoServerError
except ImportError:
    print "failed=True msg='boto required for this module'"
    sys.exit(1)


def create_et_pipeline(connection, module):
    name = module.params.get('name')
    input_bucket = module.params.get('input_bucket')
    output_bucket = module.params.get('output_bucket')
    notifications = module.params.get('notifications')
    role = module.params.get('role')
    
    connection.

    if volumes:
        for volume in volumes:
            if 'device_name' not in volume:
                module.fail_json(msg='Device name must be set for volume')
            # Minimum volume size is 1GB. We'll use volume size explicitly set to 0
            # to be a signal not to create this volume
            if 'volume_size' not in volume or int(volume['volume_size']) > 0:
                bdm[volume['device_name']] = create_block_device(module, volume)

    lc = LaunchConfiguration(
        name=name,
        image_id=image_id,
        key_name=key_name,
        security_groups=security_groups,
        user_data=user_data,
        block_device_mappings=[bdm],
        instance_type=instance_type,
        kernel_id=kernel_id,
        spot_price=spot_price,
        instance_monitoring=instance_monitoring,
        associate_public_ip_address = assign_public_ip,
        ramdisk_id=ramdisk_id,
        instance_profile_name=instance_profile_name,
        ebs_optimized=ebs_optimized,
    )

    launch_configs = connection.get_all_launch_configurations(names=[name])
    changed = False
    if not launch_configs:
        try:
            connection.create_launch_configuration(lc)
            launch_configs = connection.get_all_launch_configurations(names=[name])
            changed = True
        except BotoServerError, e:
            module.fail_json(msg=str(e))
    result = launch_configs[0]

    module.exit_json(changed=changed, name=result.name, created_time=str(result.created_time),
                     image_id=result.image_id, arn=result.launch_configuration_arn,
                     security_groups=result.security_groups, instance_type=instance_type)


def delete_et_pipeline(connection, module):
    name = module.params.get('name')
    launch_configs = connection.get_all_launch_configurations(names=[name])
    if launch_configs:
        launch_configs[0].delete()
        module.exit_json(changed=True)
    else:
        module.exit_json(changed=False)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True, type='str'),
            input_bucket=dict(type='str'),
            output_bucket=dict(type='str'),
            notifications=dict(type='dict'),
            role=dict(type='str'),
            state=dict(default='present', choices=['present', 'absent'])
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)

    try:
        connection = connect_to_aws(boto.ec2.elastictranscoder, region, **aws_connect_params)
    except (boto.exception.NoAuthHandlerFound, StandardError), e:
        module.fail_json(msg=str(e))

    state = module.params.get('state')

    if state == 'present':
        create_et_pipeline(connection, module)
    elif state == 'absent':
        delete_et_pipeline(connection, module)

main()
