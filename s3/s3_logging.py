#!/usr/bin/python
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: s3_logging
short_description: Manage logging facility of an s3 bucket in AWS
description:
    - Manage logging facility of an s3 buckets in AWS
version_added: "2.0"
author: Rob White (@wimnat)
options:
  name:
    description:
      - Name of the s3 bucket
    required: true
    default: null
  target_bucket:
    description:
      - The bucket to log to.
    required: false
    default: null
  target_prefix:
    description:
      - The prefix that should be prepended to the generated log files written to the target_bucket.
    required: false
    default: no
  state:
    description:
      - Enable or disable logging.
    required: false
    default: present
    choices: [ 'present', 'absent' ]
    
extends_documentation_fragment: aws
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Enable logging of s3 bucket mywebsite.com to s3 bucket mylogs
  s3_logging:
    name: mywebsite.com
    target_bucket: mylogs
    target_prefix: logs/mywebsite.com
    state: present

- name: Remove logging on an s3 bucket
  s3_logging:
    name: mywebsite.com
    state: absent
    
'''

import xml.etree.ElementTree as ET

try:
    import boto.ec2
    from boto.s3.connection import OrdinaryCallingFormat
    from boto.s3.tagging import Tags, TagSet
    from boto.exception import BotoServerError
    from boto.exception import S3CreateError, S3ResponseError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False
    
def get_error_message(passed_e):

    xml_string = passed_e.args[2]
    
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError, e:
        return passed_e.message
    for message in root.findall('.//Message'):            
        return message.text
    
def get_error_code(passed_e):
    
    xml_string = passed_e.args[2]
    
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError, e:
        return passed_e.error_code
    for message in root.findall('.//Code'):            
        return message.text

def compare_bucket_logging(bucket, target_bucket, target_prefix):
    
    bucket_log_obj = bucket.get_logging_status()
    if bucket_log_obj.target != target_bucket or bucket_log_obj.prefix != target_prefix:
        return False
    else:
        return True
    

def enable_bucket_logging(connection, module):
    
    bucket_name = module.params.get("name")
    target_bucket = module.params.get("target_bucket")
    target_prefix = module.params.get("target_prefix")
    if target_prefix is None:
        target_prefix = ''
    changed = False
    
    try:
        bucket = connection.get_bucket(bucket_name)
        if not compare_bucket_logging(bucket, target_bucket, target_prefix):
            # Before we can enable logging we must give the log-delivery group WRITE and READ_ACP permissions to the target bucket
            try:
                target_bucket_obj = connection.get_bucket(target_bucket)
                target_bucket_obj.set_as_logging_target()
            except S3ResponseError as e:
                module.fail_json(msg=get_error_message(e))
                
            bucket.enable_logging(target_bucket, target_prefix)
            changed = True
    except S3ResponseError as e:
        module.fail_json(msg=get_error_message(e))
    
    #module.exit_json(changed=changed, config=website_config)
    module.exit_json(changed=changed)
    
    
def disable_bucket_logging(connection, module):
    
    bucket_name = module.params.get("name")
    changed = False
    
    try:
        bucket = connection.get_bucket(bucket_name)
        if not compare_bucket_logging(bucket, None, None):
            bucket.disable_logging()
            changed = True
    except S3ResponseError as e:
        module.fail_json(msg=get_error_message(e))
   
    module.exit_json(changed=changed)
    
    
def main():
    
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name = dict(required=True, default=None),
            target_bucket = dict(required=False, default=None),
            target_prefix = dict(required=False, default=None),
            state = dict(required=False, default='present', choices=['present', 'absent'])
        )
    )
    
    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')
    
    region, ec2_url, aws_connect_params = get_aws_connection_info(module)

    if region:
        try:
            connection = connect_to_aws(boto.s3, region, **aws_connect_params)
        except (boto.exception.NoAuthHandlerFound, StandardError), e:
            module.fail_json(msg=str(e))
    else:
        module.fail_json(msg="region must be specified")

    state = module.params.get("state")

    if state == 'present':
        enable_bucket_logging(connection, module)
    elif state == 'absent':
        disable_bucket_logging(connection, module)

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>

main()