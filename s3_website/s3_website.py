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

import xml.etree.ElementTree as ET

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

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

def make_routing_rules_object(routing_rules):
    
    routing_rules_list = []
    for key, value in routing_rules.iteritems():
        if "hostname" in value:
            hostname = value.get("hostname")
        else:
            hostname = None
        if "protocol" in value:
            protocol = value.get("protocol")
        else:
            hostname = None
        if "replace_key" in value:
            replace_key = value.get("replace_key")
        else:
            replace_key = None
        if "replace_key_prefix" in value:
            replace_key_prefix = value.get("replace_key_prefix")
        else:
            replace_key_prefix = None
        if "http_redirect_code" in value:
            http_redirect_code = value.get("http_redirect_code")
        else:
            http_redirect_code = None
        
        print     
        routing_rules_list.append(RoutingRule.when(key_prefix=key).then_redirect(hostname, protocol, replace_key, replace_key_prefix, http_redirect_code))
    
    return RoutingRules(routing_rules_list)

def enable_bucket_as_website(connection, module):
    
    bucket_name = module.params.get("bucket")
    suffix = module.params.get("suffix")
    error_key = module.params.get("error_key")
    routing_rules = module.params.get("routing_rules")
    redirect_all_requests = module.params.get("redirect_all_requests")
    
    if redirect_all_requests is not None:
        redirect_location = RedirectLocation(hostname=redirect_all_requests)
    else:
        redirect_location = None
    
    if routing_rules is not None:
        routing_rules_object = make_routing_rules_object(routing_rules)
    else:
        routing_rules_object = None
    
    try:
        bucket = connection.get_bucket(bucket_name)
        bucket.configure_website(suffix, error_key, redirect_location, routing_rules_object)
        changed = True
    except BotoServerError as e:
        module.fail_json(msg=get_error_message(e.args[2]))
    
    website_config = bucket.get_website_configuration()
    module.exit_json(changed=changed, config=website_config, here="yes")
    
def disable_bucket_as_website(connection, module):
    
    bucket_name = module.params.get("bucket")
    
    try:
        bucket = connection.get_bucket(bucket_name)
        bucket.get_website_configuration()
        bucket.delete_website_configuration()
        changed = True
    except BotoServerError as e:
        msg = get_error_message(e.args[2])
        if msg == "The specified bucket does not have a website configuration":
            changed = False
        else:
            module.fail_json(msg=get_error_message(e.args[2]))
    
    module.exit_json(changed=changed, config={})
    
def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            bucket = dict(required=True),
            state = dict(default='present', choices=['present', 'absent']),
            suffix = dict(default='index.htm'),
            error_key = dict(),
            routing_rules = dict(type='dict'),
            redirect_all_requests = dict()
        ),
        #mutually_exclusive = [ 
        #                       ['redirect_all_requests', 'suffix'],
        #                       ['redirect_all_requests', 'error_key'],
        #                       ['redirect_all_requests', 'routing_rules']
        #                     ]
    )
    
    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')
    
    region, ec2_url, aws_connect_params = get_aws_connection_info(module)

    if region:
        try:
            connection = connect_to_aws(boto.s3, region, **aws_connect_params)
            #s3 = boto.s3.connect_to_region(region, is_secure=True, calling_format=OrdinaryCallingFormat(), **aws_connect_params)
        except (boto.exception.NoAuthHandlerFound, StandardError), e:
            module.fail_json(msg=str(e))
    else:
        module.fail_json(msg="region must be specified")

    state = module.params.get("state")

    if state == 'present':
        enable_bucket_as_website(connection, module)
    elif state == 'absent':
        disable_bucket_as_website(connection, module)
        

# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>

main()
