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
module: ec2_vpc_dhcp_opts
short_description: Manage AWS VPC DHCP option sets
description:
    - Manage AWS VPC DHCP option sets
version_added: "2.0"
author: Rob White (@wimnat)
options:
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

import sys  # noqa
import time

try:
    import boto.ec2
    import boto.vpc
    from boto.exception import EC2ResponseError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False
    if __name__ != '__main__':
        raise

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
            tags = dict(default=None, required=False, type='dict', aliases=['resource_tags']),
            vpc_id = dict(default=None, required=True)
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