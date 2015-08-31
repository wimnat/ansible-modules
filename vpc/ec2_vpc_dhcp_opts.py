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
from boto.exception import BotoServerError

DOCUMENTATION = '''
---
module: ec2_vpc_dhcp_opts
short_description: Manage AWS VPC DHCP option sets
description:
    - Manage AWS VPC DHCP option sets
version_added: "2.0"
author: Rob White (@wimnat)
options:
  dhcp_opt_id:
    description:
      - "DHCP options set ID"
    required: false
    default: null
  domain_name:
    description:
      - "A domain name of your choice (for example, example.com)"
    required: false
    default: null
  domain_name_servers:
    description:
      - "A list of the IP address(es) of a domain name server. You can specify up to four addresses."
    required: false
    default: null
  lookup:
    description:
      - "Look up route table by either tags or by route table ID. Non-unique tag lookup will fail. If no tags are specifed then no lookup for an existing route table is performed and a new route table will be created. To change tags of a route table, you must look up by id."
    required: false
    default: tag
    choices: [ 'tag', 'id' ]
  ntp_servers:
    description:
      - "A list of the IP address(es) of a Network Time Protocol (NTP) server. You can specify up to four addresses."
    required: false
    default: null
  netbios_name_servers:
    description:
      - "A list of the IP address(es) of a NetBIOS name server. You can specify up to four addresses."
    required: false
    default: null
  netbios_node_type:
    description:
      - "The NetBIOS node type (1, 2, 4, or 8). For more information about the values, see RFC 2132. We recommend you only use 2 at this time (broadcast and multicast are currently not supported)."
    required: false
    default: null
  state:
    description:
      - "Create or remove the DHCP option set"
    required: false
    default: present
    choices: [ 'present', 'absent' ]
  tags:
    description:
      - "A dict of tags to apply to the DHCP option set. Any tags currently applied to the set and not present here will be removed."
    required: false
    default: null
    aliases: [ 'resource_tags' ]
  vpc_id:
    description:
      - "VPC ID of the VPC you want to attach the DHCP option set to."
    required: false
    default: null
notes:
  - There is no option to modify a DHCP option set in AWS. Therefore, if you lookup by tag or ID and the options specified in the playbook do not match, the module will fail rather than make any change.    
extends_documentation_fragment: aws
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Create subnet for database servers
  ec2_vpc_dhcp_opts:
    state: present
    vpc_id: vpc-123456
    cidr: 10.0.1.16/28
    resource_tags:
      Name: Database Subnet
  register: database_subnet

- name: Remove subnet for database servers
  ec2_vpc_subnet:
    state: absent
    vpc_id: vpc-123456
    cidr: 10.0.1.16/28
    
'''

try:
    import boto.vpc
    from boto.exception import EC2ResponseError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

def get_dhcp_opt_set_by_id(connection, dhcp_opt_id):

    dhcp_opt_set = None
    dhcp_opt_sets = connection.get_all_dhcp_options(filters={'dhcp-options-id': dhcp_opt_id})
    if dhcp_opt_sets:
        dhcp_opt_set = dhcp_opt_sets[0]
    
    return dhcp_opt_set
    
def get_dhcp_opt_set_by_tags(connection, tags):
    
    count = 0
    dhcp_opt_set = None 
    dhcp_opt_sets = connection.get_all_route_tables()
    for opt_set in dhcp_opt_sets:
        if tags == opt_set.tags:
            dhcp_opt_set = opt_set
            count +=1
    
    if count > 1:
        raise RuntimeError("Tags provided do not identify a unique DHCP option set")
    else:        
        return dhcp_opt_set

def ensure_dhcp_opts_set_present(connection, module):
    
    lookup = module.params.get('lookup')
    dhcp_opt_id = module.params.get('dhcp_opt_id')
    domain_name = module.params.get('domain_name')
    domain_name_servers = module.params.get('domain_name_servers')
    ntp_servers = module.params.get('ntp_servers')
    netbios_name_servers = module.params.get('netbios_name_servers')
    netbios_node_type = module.params.get('netbios_node_type')
    tags = module.params.get('tags')
    check_mode = module.params.get('check_mode')
    
    if lookup == 'tag':
        if tags is not None:
            try:
                dhcp_option_set = get_dhcp_opt_set_by_tags(connection, tags)
            except EC2ResponseError as e:
                module.fail_json(msg=e.message)
            except RuntimeError as e:
                module.fail_json(msg=e.args[0])
        else:
            dhcp_option_set = None
    elif lookup == 'id':
        try:
            dhcp_option_set = get_dhcp_opt_set_by_id(connection, vpc_id, route_table_id)
        except EC2ResponseError as e:
            module.fail_json(msg=e.message)
            
    if dhcp_option_set:
        continue
        #print dhcp_option_set.__dict__
    else:
        try:
            dhcp_option_set = connection.create_dhcp_options(domain_name, domain_name_servers, ntp_servers, netbios_name_servers, netbios_node_type, dry_run=check_mode)
        except BotoServerError as e:
            module.fail_json(msg=e.message)
        
    print dhcp_option_set.__dict__

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            lookup = dict(default='tag', required=False, choices=['tag', 'id']),
            domain_name = dict(default=None, required=False, type='str'),
            domain_name_servers = dict(default=None, required=False, type='list'),
            ntp_servers = dict(default=None, required=False, type='list'),
            netbios_name_servers = dict(default=None, required=False, type='list'),
            netbios_node_type = dict(default=None, required=False, type='str', choices=['1','2','4','8']),
            state = dict(default='present', choices=['present', 'absent']),
            tags = dict(default=None, required=False, type='dict', aliases=['resource_tags'])
        )
    )
    
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    
    if not HAS_BOTO:
        module.fail_json(msg='boto is required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)
    
    if region:
        try:
            connection = connect_to_aws(boto.vpc, region, **aws_connect_params)
        except (boto.exception.NoAuthHandlerFound, StandardError), e:
            module.fail_json(msg=str(e))
    else:
        module.fail_json(msg="region must be specified")

    lookup = module.params.get('lookup')
    route_table_id = module.params.get('route_table_id')
    state = module.params.get('state', 'present')
    
    if state == 'present':
        ensure_dhcp_opts_set_present(connection, module)
    elif state == 'absent':
        ensure_dhcp_opts_set_absent(connection, module)
        
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()