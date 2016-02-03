#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: iam_role
short_description: Manage AWS IAM roles
description:
  - Manage AWS IAM roles
version_added: "2.1"
author: Rob White, @wimnat
options:
  path:
    description:
      - The path to the role. For more information about paths, see U(http://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html).
    required: false
    default: "/"
  name:
    description:
      - The name of the role to create.
    required: true
  assume_role_policy_document:
    description:
      - Number of seconds to wait
    required: false
  managed_policy:
    description:
      - A list of managed policies to attach to the role. To embed an inline policy, use M(iam_policy). To remove existing policies, use an empty list item.
    required: false
  state:
    description:
      - Create or remove the IAM role
    required: true
    choices: [ 'present', 'absent' ]
requirements: [ botocore, boto3 ]
extends_documentation_fragment:
  - aws
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create a role
- iam_role:
    name: mynewrole
    assume_role_policy_document: lookup()
    state: present

# Create a role and attach a managed policy called "PowerUserAccess"
- iam_role:
    name: mynewrole
    assume_role_policy_document: lookup()
    state: present
    managed_policy:
      - PowerUserAccess

# Keep the role created above but remove all managed policies
- iam_role:
    name: mynewrole
    assume_role_policy_document: lookup()
    state: present
    managed_policy:
      -

# Delete the role
- iam_role:
    name: mynewrole
    assume_role_policy_document: lookup()
    state: absent

'''
RETURN = '''
activeServicesCount:
    description: how many services are active in this cluster
    returned: 0 if a new cluster
    type: int
clusterArn:
    description: the ARN of the cluster just created
    type: string (ARN)
    sample: arn:aws:ecs:us-west-2:172139249013:cluster/test-cluster-mfshcdok
clusterName:
    description: name of the cluster just created (should match the input argument)
    type: string
    sample: test-cluster-mfshcdok
pendingTasksCount:
    description: how many tasks are waiting to run in this cluster
    returned: 0 if a new cluster
    type: int
registeredContainerInstancesCount:
    description: how many container instances are available in this cluster
    returned: 0 if a new cluster
    type: int
runningTasksCount:
    description: how many tasks are running in this cluster
    returned: 0 if a new cluster
    type: int
status:
    description: the status of the new cluster
    returned: ACTIVE
    type: string
'''

import json

try:
    from botocore.exceptions import ClientError
except ImportError:
    HAS_BOTOCORE = False

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

def create_role(connection, module):

    params = dict()
    params['Path'] = module.params.get('path')
    params['RoleName'] = module.params.get('name')
    params['AssumeRolePolicyDocument'] = module.params.get('assume_role_policy_document')
    role = get_role(connection, params['RoleName'])

    if not compare_role(params, role):
        # Remove any items with a value of None
        for k,v in list(params.items()):
            if v is None:
                del params[k]
        try:
            params['AssumeRolePolicyDocument'] = json.dumps(params['AssumeRolePolicyDocument'])
            role = connection.create_role(**params)
        except (botocore.exceptions.ClientError, botocore.exceptions.ParamValidationError) as e:
            module.fail_json(msg=e.message)

    if compare_managed_policies(connection, module, role):
        module.exit_json(changed=True, **role)


def destroy_role(connection, module):

    params = dict()
    params['RoleName'] = module.params.get('name')

    if get_role(connection, params['RoleName']):
        try:
            connection.delete_role(**params)
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=e.message)
    else:
        module.exit_json(changed=False)

    module.exit_json(changed=True)


def get_role(connection, name):

    params = dict()
    params['RoleName'] = name

    try:
        return connection.get_role(**params)['Role']
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            return None
        else:
            module.fail_json(msg=e.message)


def compare_role(role_params, existing_role):

    role_params['AssumeRolePolicyDocument'] = json.loads(role_params['AssumeRolePolicyDocument'])

    if existing_role is not None:
        # We don't need all the returned params so just get the ones we need
        existing_role_params = {}
        existing_role_params['Path'] = existing_role['Path']
        existing_role_params['RoleName'] = existing_role['RoleName']
        existing_role_params['AssumeRolePolicyDocument'] = existing_role['AssumeRolePolicyDocument']

        if existing_role_params == role_params:
            return True
        else:
            return False
    else:
        return False


def compare_managed_policies(connection, module, role):

    policy_iterator = role.attached_policies.all()
    for policy in policy_iterator:
        print "x"
        print policy


def main():

    # Default document for a new role
    default_document = "{ \"Version\": \"2012-10-17\", \"Statement\": [{ \"Sid\": \"\", \"Effect\": \"Allow\", \"Principal\": { \"Service\": \"ec2.amazonaws.com\" }, \"Action\": \"sts:AssumeRole\" }] }"
    #default_document['Version'] = '2012-10-17'
    #default_document['Statement'] = [{}]
    #default_document['Statement'][0]['Sid'] = ''
    #default_document['Statement'][0]['Effect'] = 'Allow'
    #default_document['Statement'][0]['Principal'] = {}
    #default_document['Statement'][0]['Principal']['Service'] = 'ec2.amazonaws.com'
    #default_document['Statement'][0]['Action'] = 'sts:AssumeRole'

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name = dict(required=True, type='str'),
            path = dict(default="/", required=False, type='str'),
            assume_role_policy_document = dict(default=default_document, required=False),
            state = dict(default=None, choices=['present', 'absent'], required=True)
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    connection = boto3_conn(module, conn_type='client', resource='iam', region=region, endpoint=ec2_url, **aws_connect_params)

    state = module.params.get("state")

    if state == 'present':
        create_role(connection, module)
    else:
        destroy_role(connection, module)

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
