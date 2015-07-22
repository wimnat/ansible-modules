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
module: ec2_vpc_route_table_facts
short_description: Gather facts about ec2 VPC route tables in AWS
description:
    - Gather facts about ec2 VPC route tables in AWS
version_added: "2.0"
author: "Rob White (@wimnat)"
options:
  route_table_id:
    description:
      - The ID of the route table. Pass this option to gather facts about a particular route table.
    required: false
    default: null

extends_documentation_fragment: aws
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather facts about all VPC route tables
- ec2_vpc_route_table_facts:

# Gather facts about a particular VPC route table
- ec2_vpc_route_table_facts:
    route_table_id: rtb-00112233

'''

try:
    import boto.vpc
    from boto.exception import BotoServerError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

def get_route_table_info(route_table):

    # Add any routes to array
    routes = []
    for route in route_table.routes:
        routes.append(route.__dict__)

    route_table_info = { 'id': route_table.id,
                         'routes': routes,
                         'tags': route_table.tags,
                         'vpc_id': route_table.vpc_id
                       }

    return route_table_info

def list_ec2_vpc_route_tables(connection, module):

    route_table_id = module.params.get("route_table_id")
    route_table_dict_array = []

    try:
        all_route_tables = connection.get_all_route_tables(route_table_id)
    except BotoServerError as e:
        module.fail_json(msg=e.message)

    for route_table in all_route_tables:
        route_table_dict_array.append(get_route_table_info(route_table))

    module.exit_json(route_tables=route_table_dict_array)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            route_table_id = dict(default=None)
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)

    if region:
        try:
            connection = connect_to_aws(boto.vpc, region, **aws_connect_params)
        except (boto.exception.NoAuthHandlerFound, StandardError), e:
            module.fail_json(msg=str(e))
    else:
        module.fail_json(msg="region must be specified")

    list_ec2_vpc_route_tables(connection, module)

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()