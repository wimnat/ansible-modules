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
module: s3_cors
short_description: Manage s3 bucket CORS (Cross-Origin Resource Sharing) rules in AWS
description:
    - Manage s3 bucket CORS (Cross-Origin Resource Sharing) rules in AWS
version_added: "2.0"
author: Rob White (@wimnat)
options:
  name:
    description:
      - Name of the s3 bucket
    required: true
    default: null
  allowed_header:
    description:
      - Specifies which headers are allowed in a pre-flight OPTIONS request via the Access-Control-Request-Headers header. Each header name specified in the Access-Control-Request-Headers header must have a corresponding entry in the rule. Amazon S3 will send only the allowed headers in a response that were requested. This can contain at most one * wild character.
    required: true
    default: null
  allowed_methods:
    description:
      - An HTTP method that you want to allow the origin to execute. At least one method must be specified.
    required: true
    default: null
    choices: [ 'get', 'put', 'head', 'post', 'delete' ]
  allowed_origin:
    description:
      - An origin that you want to allow cross-domain requests from. This can contain at most one * wild character.
      required: true
      default: null
  rule_id:
    description:
      - Unique identifier for the rule. The value cannot be longer than 255 characters. A unique value for the rule will be generated if no value is provided.
      required: true
      default: null
  state:
    description:
      - Create or remove the CORS rule
    required: false
    default: present
    choices: [ 'present', 'absent' ]
  max_age_seconds:
    description:
      - Time in seconds that the browser should cache the pre-flight response for the specified resource.
    required: false
    default: null
  expose_header:
    description:
      - One or more headers in the response that you want customers to be able to access from their applications (for example, from a JavaScript XMLHttpRequest object). You add one ExposeHeader element in the rule for each header.
    required: false
    default: null

extends_documentation_fragment: aws
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.


    
'''

import xml.etree.ElementTree as ET

try:
    import boto.ec2
    from boto.s3.connection import OrdinaryCallingFormat
    from boto.s3.cors import CORSRule, CORSConfiguration
    from boto.exception import BotoServerError
    from boto.exception import S3CreateError, S3ResponseError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False
    
class CommonEqualityMixin(object):
    
    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)

class Rule(Rule):

    def __eq__(self, other):
        
        return self.__dict__ == other.__dict__
        #return self.status == other.status
        #return (isinstance(other, self.__class__)
        #    and self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)
    
class Expiration(Expiration):

    def __eq__(self, other):
        return self.__dict__ == other.__dict__
        #return (isinstance(other, self.__class__)
        #    and self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)
    
class Transition(Transition):

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)        

def get_error_message(passed_e):
    
    xml_string = passed_e.args[2]
    
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError, e:
        return passed_e
    for message in root.findall('.//Message'):            
        return message.text
    
def get_error_code(passed_e):
    
    xml_string = passed_e.args[2]
    
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError, e:
        return passed_e
    for message in root.findall('.//Code'):            
        return message.text


def create_cors_rule(connection, module):

    name = module.params.get("name")
    allowed_header = module.params.get("allowed_header")
    allowed_methods = module.params.get("allowed_methods")
    allowed_origin = module.params.get("allowed_origin")
    rule_id = module.params.get("rule_id")
    max_age_seconds = module.params.get("max_age_seconds")
    expose_header = module.params.get("expose_header")
    changed = False

    try:
        bucket = connection.get_bucket(name)
    except S3ResponseError, e:
        module.fail_json(msg=str(get_error_message(e)))

    # Get the bucket's current CORS rules
    try:
        current_lifecycle_obj = bucket.get_cors()
        error_code = get_error_code(e.args[2])
    except S3ResponseError, e:
        if error_code == "NoSuchLifecycleConfiguration":
            current_cors_obj = CORSConfiguration()
        else:
            module.fail_json(msg=str(get_error_message(e)))

    # Create CORS rule
    cors_rule = CORSRule(allowed_method=allowed_methods, allowed_origin=allowed_origin, id=rule_id, allowed_header=allowed_header, max_age_seconds=max_age_seconds, expose_header=expose_header)

    # Create lifecycle
    cors_obj = CORSConfiguration()
    
    # Check if rule exists
    # If an ID exists, use that otherwise compare based on prefix
    if rule.id is not None:
        for existing_rule in current_lifecycle_obj:
            if rule.id != existing_rule.id:
                lifecycle_obj.append(existing_rule)
            else:
                lifecycle_obj.append(rule)
    else:
        appended = False
        for existing_rule in current_lifecycle_obj:
            # Drop the rule ID and Rule object for comparison purposes
            existing_rule.id = None
            del existing_rule.Rule
            
            if rule.prefix == existing_rule.prefix:
                if rule == existing_rule:
                    lifecycle_obj.append(rule)
                    appended = True
                else:
                    lifecycle_obj.append(rule)
                    changed = True
                    appended = True
            else:
                lifecycle_obj.append(existing_rule)
    
    if not appended:
        lifecycle_obj.append(rule)
        changed = True
        
    # Write lifecycle to bucket
    try:
        bucket.configure_lifecycle(lifecycle_obj)
    except BotoServerError, e:
        module.fail_json(msg=str(get_error_message(e.args[2])))
        
    module.exit_json(changed=changed)
    
def destroy_lifecycle_rule(connection, module):

    name = module.params.get("name")
    prefix = module.params.get("prefix")
    rule_id = module.params.get("rule_id")
    changed = False

    try:
        bucket = connection.get_bucket(name)
    except S3ResponseError, e:
        module.fail_json(msg=str(get_error_message(e.args[2])))

    # Get the bucket's current lifecycle rules
    try:
        current_lifecycle_obj = bucket.get_lifecycle_config()
    except S3ResponseError, e:
        module.fail_json(msg=str(get_error_message(e.args[2])))
        
    # Create lifecycle
    lifecycle_obj = Lifecycle()
    
    # Check if rule exists
    # If an ID exists, use that otherwise compare based on prefix
    if rule_id is not None:
        for existing_rule in current_lifecycle_obj:
            if rule_id == existing_rule.id:
                # We're not keeping the rule (i.e. deleting) so mark as changed
                changed = True
            else:
                lifecycle_obj.append(existing_rule)
    else:
        for existing_rule in current_lifecycle_obj:
            if prefix == existing_rule.prefix:
                # We're not keeping the rule (i.e. deleting) so mark as changed
                changed = True
            else:
                lifecycle_obj.append(existing_rule)
                
    
    # Write lifecycle to bucket or, if there no rules left, delete lifecycle configuration
    try:
        if lifecycle_obj:
            bucket.configure_lifecycle(lifecycle_obj)
        else:
            bucket.delete_lifecycle_configuration()
    except BotoServerError, e:
        module.fail_json(msg=str(get_error_message(e.args[2])))
        
    module.exit_json(changed=changed)
    

def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name = dict(required=True),
            allowed_header = dict(default=None, required=False, type='list'),
            allowed_methods = dict(default=None, required=True, choices=['get', 'put', 'head', 'post', 'delete']),
            allowed_origin = dict(default='no', required=True, type='str'),
            rule_id = dict(default=None, required=False),
            state = dict(default='present', choices=['present', 'absent']),
            max_age_seconds = dict(default=None, type='int'),
            expose_header = dict(default=None)
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
        create_cors_rule(connection, module)
    elif state == 'absent':
        destroy_cors_rule(connection, module)

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>

main()