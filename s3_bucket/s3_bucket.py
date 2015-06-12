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
from boto.exception import S3CreateError, S3ResponseError

DOCUMENTATION = '''
---
module: s3_bucket
short_description: Manage s3 buckets in AWS
description:
    - Manage s3 buckets in AWS
version_added: "2.0"
author: Rob White, wimnat [at] gmail.com, @wimnat
options:
  policy:
    description:
      - The JSON policy as a string.
    required: false
    default: null
  name:
    description:
      - Name of the s3 bucket
    required: false
    default: null
  requestor_pays
    description:
      - With Requester Pays buckets, the requester instead of the bucket owner pays the cost of the request and the data download from the bucket.
    required: false
    default: no
    choices: [ 'yes', 'no' ]
  state:
    description:
      - Create or remove the s3 bucket
    required: false
    default: present
    choices: [ 'present', 'absent' ]
  versioning:
    description: 
      - Whether versioning is enabled or disabled (note that once versioning is enabled, it can only be suspended)
    required: false
    default: no
    choices: [ 'yes', 'no' ]
    
extends_documentation_fragment: aws
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Create an s3 bucket
  s3_bucket:
    name: mys3bucket
    state: present

- name: Remove an s3 bucket
  s3_bucket:
    name: mys3bucket
    state: absent
    
'''

import xml.etree.ElementTree as ET

try:
    import boto.ec2
    from boto.s3.connection import OrdinaryCallingFormat
    from boto.s3.website import RedirectLocation
    from boto.s3.website import RoutingRules
    from boto.s3.website import RoutingRule
    from boto.exception import BotoServerError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False
    
def get_error_message(xml_string):
    
    root = ET.fromstring(xml_string)
    for message in root.findall('.//Message'):            
        return message.text
    
def get_error_code(xml_string):
    
    root = ET.fromstring(xml_string)
    for message in root.findall('.//Code'):            
        return message.text

def get_location(region):
    
    if region == "us-west-1":
        return "USWest"
    elif region == "us-west-2":
        return "USWest2"
    else:
        return "DEFAULT"

def get_request_payment_status(bucket):
    
    response = bucket.get_request_payment()
    root = ET.fromstring(response)
    for message in root.findall('.//{http://s3.amazonaws.com/doc/2006-03-01/}Payer'):
        payer = message.text
    
    if payer == "BucketOwner":
        return False
    else:
        return True

def create_bucket(connection, module):
    
    policy = module.params.get("policy")
    name = module.params.get("name")
    region = module.params.get("region")
    versioning = module.params.get("versioning")
    requester_pays = module.params.get("requester_pays")
    changed = False
    
    try:
        bucket = connection.get_bucket(name)
    except S3ResponseError, e:
        try:
            bucket = connection.create_bucket(name, location=region)
            changed = True
        except Exception, e:
            module.fail_json(msg=str(get_error_message(e.args[2])))
    
    # Versioning
    versioning_status = bucket.get_versioning_status()
    if not versioning_status and versioning:
        try:
            bucket.configure_versioning(versioning)
            changed = True
            versioning_status = bucket.get_versioning_status()
        except Exception, e:
            module.fail_json(msg=str(get_error_message(e.args[2])))
    elif not versioning_status and not versioning:
        # do nothing
        pass
    else:
        if versioning_status['Versioning'] == "Enabled" and not versioning:
            bucket.configure_versioning(versioning)
            changed = True
            versioning_status = bucket.get_versioning_status()
        elif ( (versioning_status['Versioning'] == "Disabled" and versioning) or (versioning_status['Versioning'] == "Suspended" and versioning) ):
            bucket.configure_versioning(versioning)
            changed = True
            versioning_status = bucket.get_versioning_status()
    
    # Requester pays
    requester_pays_status = get_request_payment_status(bucket)
    if requester_pays_status != requester_pays:
        if requester_pays:
            bucket.set_request_payment(payer='Requester')
            changed = True
            requester_pays_status = get_request_payment_status(bucket)
        else:
            bucket.set_request_payment(payer='BucketOwner')
            changed = True
            requester_pays_status = get_request_payment_status(bucket)

    # Policy        
    try:
        current_policy = bucket.get_policy()
    except S3ResponseError, e:
        error_code = get_error_code(e.args[2])
        if error_code == "NoSuchBucketPolicy":
            current_policy = None
        else:
            module.fail_json(debug=x, msg=str(get_error_message(e.args[2])))
    
    if current_policy is not None and policy is not None:
        x = "1"
        if policy is not None:
            policy = json.dumps(policy)
            
        if json.loads(current_policy) != json.loads(policy):
            try:
                bucket.set_policy(policy)
                changed = True
                current_policy = bucket.get_policy()
            except S3ResponseError, e:
                module.fail_json(msg=str(get_error_message(e.args[2])))

    elif current_policy is None and policy is not None:
        x = "2"
        policy = json.dumps(policy)
            
        try:
            bucket.set_policy(policy)
            changed = True
            current_policy = bucket.get_policy()
        except S3ResponseError, e:
            module.fail_json(msg=str(get_error_message(e.args[2])))
    
    elif current_policy is not None and policy is None:
        x = "3"
        try:
            bucket.delete_policy()
            changed = True
            current_policy = bucket.get_policy()
        except S3ResponseError, e:
            error_code = get_error_code(e.args[2])
            if error_code == "NoSuchBucketPolicy":
                current_policy = None
            else:
                module.fail_json(msg=str(get_error_message(e.args[2])))
    else:
        x = "4"
            
    ####
    ## Fix up json of policy so it's not escaped
    ####        
    module.exit_json(debug=x, changed=changed, name=bucket.name, versioning=versioning_status, requester_pays=requester_pays_status, policy=current_policy)
    
def destroy_bucket(connection, module):
    
    name = module.params.get("name")
    changed = False
    
    try:
        bucket = connection.delete_bucket(name)
        changed = True
        print bucket
    except Exception, e:
        module.fail_json(msg=str(e))
        
    
    
def main():
    
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            policy = dict(required=False, default=None),
            name = dict(required=True),
            requester_pays = dict(default='no', type='bool'),
            state = dict(default='present', choices=['present', 'absent']),
            versioning = dict(default='no', type='bool')
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
        create_bucket(connection, module)
    elif state == 'absent':
        destroy_bucket(connection, module)

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>

main()