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
module: s3_bucket
short_description: Manage s3 buckets in AWS
description:
    - Manage s3 buckets in AWS
version_added: "2.0"
author: Rob White (@wimnat)
options:
  force:
    description: 
      - When trying to delete a bucket, delete all keys in the bucket first (an s3 bucket must be empty for a successful deletion)
    required: false
    default: no
    choices: [ 'yes', 'no' ]
  name:
    description:
      - Name of the s3 bucket
    required: true
    default: null
  policy:
    description:
      - The JSON policy as a string.
    required: false
    default: null
  region:
    description:
      - The AWS region to use.  Must be specified if ec2_url is not used. If not specified then the value of the EC2_REGION environment variable, if any, is used. See U(http://docs.aws.amazon.com/general/latest/gr/rande.html#ec2_region)
    required: false
    default: null
    aliases: [ 'aws_region', 'ec2_region' ]
  requestor_pays:
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
  tags:
    description:
      - tags dict to apply to bucket
    required: false
    default: null
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
    from boto.s3.tagging import Tags, TagSet
    from boto.exception import BotoServerError, S3CreateError, S3ResponseError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

def get_request_payment_status(bucket):
    
    response = bucket.get_request_payment()
    root = ET.fromstring(response)
    for message in root.findall('.//{http://s3.amazonaws.com/doc/2006-03-01/}Payer'):
        payer = message.text
    
    if payer == "BucketOwner":
        return False
    else:
        return True

def create_tags_container(tags):

    tag_set = TagSet()
    tags_obj = Tags()
    for key, val in tags.iteritems():
        tag_set.add_tag(key, val)

    tags_obj.add_tag_set(tag_set)
    return tags_obj

def create_bucket(connection, module):
    
    policy = module.params.get("policy")
    name = module.params.get("name")
    region = module.params.get("region")
    requester_pays = module.params.get("requester_pays")
    tags = module.params.get("tags")
    versioning = module.params.get("versioning")
    changed = False
    
    try:
        bucket = connection.get_bucket(name)
    except S3ResponseError, e:
        try:
            bucket = connection.create_bucket(name, location=region)
            changed = True
        except S3CreateError, e:
            module.fail_json(msg=e.message)
    
    # Versioning
    versioning_status = bucket.get_versioning_status()
    if not versioning_status and versioning:
        try:
            bucket.configure_versioning(versioning)
            changed = True
            versioning_status = bucket.get_versioning_status()
        except S3ResponseError, e:
            module.fail_json(msg=e.message)
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
        if e.error_code == "NoSuchBucketPolicy":
            current_policy = None
        else:
            module.fail_json(msg=e.message)
    
    if current_policy is not None and policy is not None:
        if policy is not None:
            policy = json.dumps(policy)
            
        if json.loads(current_policy) != json.loads(policy):
            try:
                bucket.set_policy(policy)
                changed = True
                current_policy = bucket.get_policy()
            except S3ResponseError, e:
                module.fail_json(msg=e.message)

    elif current_policy is None and policy is not None:
        policy = json.dumps(policy)
            
        try:
            bucket.set_policy(policy)
            changed = True
            current_policy = bucket.get_policy()
        except S3ResponseError, e:
            module.fail_json(msg=e.message)
    
    elif current_policy is not None and policy is None:
        try:
            bucket.delete_policy()
            changed = True
            current_policy = bucket.get_policy()
        except S3ResponseError, e:
            if e.error_code == "NoSuchBucketPolicy":
                current_policy = None
            else:
                module.fail_json(msg=e.message)
            
    ####
    ## Fix up json of policy so it's not escaped
    ####
    
    # Tags
    try:
        current_tags = bucket.get_tags()
        tag_set = TagSet()
    except S3ResponseError, e:
        if e.error_code == "NoSuchTagSet":
            current_tags = None
        else:
            module.fail_json(msg=e.message)
    
    if current_tags is not None or tags is not None:
       
        if current_tags is None:
            current_tags_dict = {}
        else:
            current_tags_dict = dict((t.key, t.value) for t in current_tags[0])

        if sorted(current_tags_dict) != sorted(tags):
            try:
                if tags:
                    bucket.set_tags(create_tags_container(tags))
                else:
                    bucket.delete_tags()
                current_tags_dict = tags
                changed = True
            except S3ResponseError, e:
                module.fail_json(msg=e.message)

    module.exit_json(changed=changed, name=bucket.name, versioning=versioning_status, requester_pays=requester_pays_status, policy=current_policy, tags=current_tags_dict)
    
def destroy_bucket(connection, module):
    
    force = module.params.get("force")
    name = module.params.get("name")
    changed = False
    
    try:
        bucket = connection.get_bucket(name)
    except S3ResponseError, e:
        if e.error_code != "NoSuchBucket":
            module.fail_json(msg=e.message)
        else:
            # Bucket already absent
            module.exit_json(changed=changed)
    
    if force:
        try:
            # Empty the bucket
            for key in bucket.list():
                key.delete()
                
        except BotoServerError, e:
            module.fail_json(msg=e.message)
    
    try:
        bucket = connection.delete_bucket(name)
        changed = True
    except S3ResponseError, e:
        module.fail_json(msg=e.message)
        
    module.exit_json(changed=changed)
    
def main():
    
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            force = dict(required=False, default='no', type='bool'),
            policy = dict(required=False, default=None),
            name = dict(required=True),
            requester_pays = dict(default='no', type='bool'),
            state = dict(default='present', choices=['present', 'absent']),
            tags = dict(required=None, default={}, type='dict'),
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
