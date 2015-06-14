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
module: s3_website
short_description: Configure an s3 bucket as a website
description:
    - Configure an s3 bucket as a website, including redirect rules
version_added: "1.9"
author: Rob White
options:
  bucket:
    description:
      - s3 bucket name
    required: true
    default: null 
    aliases: []
  error_key:
    description:
      - The object key name to use when a 4XX class error occurs. To remove an error key, set to None.
    required: false
    default: null
    aliases: []
  redirect_all_requests:
    description:
      - Describes the redirect behavior for every request to this s3 bucket website endpoint 
    required: false
    default: null
    aliases: []
  routing_rules:
    description:
      - A dictionary of dictionaries that specifies conditions and redirects that apply when conditions are met. See examples for routing_rules values
    required: false
    default: null
    aliases: []
  state:
    description:
      - Create or delete ENI
    required: false
    default: present
  suffix:
    description:
      - Suffix that is appended to a request that is for a directory on the website endpoint (e.g. if the suffix is index.html and you make a request to samplebucket/images/ the data that is returned will be for the object with the key name images/index.html). The suffix must not be empty and must not include a slash character.
    required: false
    default: null
    aliases: []
extends_documentation_fragment: aws
requirements: [ "boto" ]

'''

EXAMPLES = '''
# Configure an s3 bucket to redirect all requests to example.com
- s3_website:
    bucket: mybucket.com
    redirect_all_requests: example.com
    state: present

# Remove website configuration from an s3 bucket
- s3_website:
    bucket: mybucket.com
    state: absent
    
# Configure an s3 bucket as a website with index and error pages and a routing rule set
- s3_website:
    bucket: mybucket.com
    suffix: index.htm
    error_key: errors/404.htm
    routing_rules:
      docs/:
        replace_key_prefix: documents/
      blog/:
        hostname: blogspace.com
    state: present
    
'''

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
    if error_key == "None":
        error_key = None
    routing_rules = module.params.get("routing_rules")
    redirect_all_requests = module.params.get("redirect_all_requests")
    changed = False
    
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
        if compare_bucket_as_website(bucket, module) is False:
            bucket.delete_website_configuration()
            bucket.configure_website(suffix, error_key, redirect_location, routing_rules_object)
            changed = True
    except BotoServerError as e:
        module.fail_json(msg=get_error_message(e.args[2]))
    
    website_config = get_website_conf_plus(bucket)
    module.exit_json(changed=changed, config=website_config)
    
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
    
def compare_bucket_as_website(bucket, module):
    
    suffix = module.params.get("suffix")
    error_key = module.params.get("error_key")
    routing_rules = module.params.get("routing_rules")
    redirect_all_requests = module.params.get("redirect_all_requests")

    try:
        website_config = bucket.get_website_configuration()
        bucket_equal = False
        
        #print "error key *******"
        #print website_config
        
        try:
            if suffix == website_config.IndexDocument.Suffix or suffix is None:
                bucket_equal = True
            else:
                bucket_equal = False
        except AttributeError:
            if suffix is None:
                bucket_equal = True
            else:
                bucket_equal = False
                
        try:
            if error_key == website_config.ErrorDocument.Key or error_key is None:
                bucket_equal = True
            else:
                bucket_equal = False
                # Check if error_key is blank. If it is, change it to none so a configure_website call will succeed
                if error_key == "":
                    module.params['error_key'] = None
        except AttributeError:
            if error_key is None:
                bucket_equal = True
            else:
                bucket_equal = False
        
        # Only check if redirect_all_requests is not None
        if redirect_all_requests is not None:
            try:
                if redirect_all_requests == website_config.RedirectAllRequestsTo.HostName:
                    bucket_equal = True
                else:
                    bucket_equal = False
            except AttributeError:
                bucket_equal = False
        
    except BotoServerError as e:
        msg = get_error_message(e.args[2])
        if msg == "The specified bucket does not have a website configuration":
            bucket_equal = False
     
    return bucket_equal

def get_website_conf_plus(bucket):
    
    website_config = bucket.get_website_configuration()
    website_config['EndPoint'] = bucket.get_website_endpoint()
    return website_config
            
    
def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            bucket = dict(required=True),
            state = dict(default='present', choices=['present', 'absent']),
            suffix = dict(),
            error_key = dict(),
            routing_rules = dict(type='dict'),
            redirect_all_requests = dict()
        )
    )
    
    module = AnsibleModule(argument_spec=argument_spec,
        mutually_exclusive = [
                               ['redirect_all_requests', 'suffix'],
                               ['redirect_all_requests', 'error_key'],
                               ['redirect_all_requests', 'routing_rules']
                             ])

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
        enable_bucket_as_website(connection, module)
    elif state == 'absent':
        disable_bucket_as_website(connection, module)
        

# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>

main()
