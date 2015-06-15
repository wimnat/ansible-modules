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
module: s3_lifecycle
short_description: Manage s3 bucket lifecycle rules in AWS
description:
    - Manage s3 bucket lifecycle rules in AWS
version_added: "2.0"
author: Rob White, wimnat [at] gmail.com, @wimnat
options:
  name:
    description:
      - Name of the s3 bucket
    required: true
    default: null
  expiration:
    description:
      - Indicates the lifetime, in days, of the objects that are subject to the rule. The value must be a non-zero positive integer.
    required: true
    default: null
  prefix:
    description:
      - Prefix identifying one or more objects to which the rule applies.
      required: false
      default: null
  rule_id:
    description:
      - Unique identifier for the rule. The value cannot be longer than 255 characters. A unique value for the rule will be generated if no value is provided.
      required: false
      default: null
  state:
    description:
      - Create or remove the lifecycle rule
    required: false
    default: present
    choices: [ 'present', 'absent' ]
  status:
    description:
      - If 'enabled', the rule is currently being applied. If 'disabled', the rule is not currently being applied.
    required: false
    default: enabled
    choices: [ 'enabled', 'disabled' ]
  storage_class:
    description:
      - The storage class to transition to. Currently there is only one valid value - 'glacier'.
    required: false
    default: glacier
    choices: [ 'glacier' ]
  transition:
    description:
      - Indicates when, in days, an object transitions to a different storage class.
    required: false
    default: null

extends_documentation_fragment: aws
'''

import xml.etree.ElementTree as ET

try:
    import boto.ec2
    from boto.s3.connection import OrdinaryCallingFormat
    from boto.s3.lifecycle import Lifecycle, Expiration, Transition, Rule
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

def get_error_message(xml_string):

    root = ET.fromstring(xml_string)
    for message in root.findall('.//Message'):
        return message.text

def get_error_code(xml_string):

    root = ET.fromstring(xml_string)
    for message in root.findall('.//Code'):
        return message.text


def create_lifecycle_rule(connection, module):

    name = module.params.get("name")
    expiration = module.params.get("expiration")
    prefix = module.params.get("prefix")
    rule_id = module.params.get("rule_id")
    status = module.params.get("status")
    storage_class = module.params.get("storage_class")
    transition = module.params.get("transition")
    changed = False

    try:
        bucket = connection.get_bucket(name)
    except S3ResponseError, e:
        module.fail_json(msg=str(get_error_message(e.args[2])))

    # Get the bucket's current lifecycle rules
    try:
        current_lifecycle_obj = bucket.get_lifecycle_config()
    except S3ResponseError, e:
        error_code = get_error_code(e.args[2])
        if error_code == "NoSuchLifecycleConfiguration":
            current_lifecycle_obj = Lifecycle()
        else:
            module.fail_json(debug=x, msg=str(get_error_message(e.args[2])))

    # Create expiration
    if expiration is not None:
        expiration_obj = Expiration(days=expiration)
    else:
        expiration_obj = None
    
    # Create transition
    if transition is not None:
        transition_obj = Transition(days=transition, storage_class=storage_class.upper())
    else:
        transition_obj = None
    
    # Create rule
    rule = Rule(rule_id, prefix, status.title(), expiration_obj, transition_obj)
    
    # Create lifecycle
    lifecycle_obj = Lifecycle()
    
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
            expiration = dict(default=None, required=False, type='int'),
            prefix = dict(default=None, required=False),
            requester_pays = dict(default='no', type='bool'),
            rule_id = dict(required=False),
            state = dict(default='present', choices=['present', 'absent']),
            status = dict(default='enabled', choices=['enabled', 'disabled']),
            storage_class = dict(default='glacier', choices=['glacier']),
            transition = dict(default=None, required=False, type='int')
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
        create_lifecycle_rule(connection, module)
    elif state == 'absent':
        destroy_lifecycle_rule(connection, module)

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>

main()