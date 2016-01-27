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
version_added: "2.1"
author: Rob White (@wimnat)
options:
  name:
    description:
      - Name of the s3 bucket to apply the CORS rules to
    required: true
    default: null
  allowed_headers:
    description:
      - A list of one or more headers that are allowed in a pre-flight OPTIONS request via the Access-Control-Request-Headers header. Each header name specified in the Access-Control-Request-Headers header must have a corresponding entry in the rule. Amazon S3 will send only the allowed headers in a response that were requested. This can contain at most one * wild character.
    required: true
    default: null
  allowed_methods:
    description:
      - A list of one or more HTTP methods that the domain/origin specified in the rule is allowed to execute. At least one method must be specified.
    required: true
    default: null
    choices: [ 'get', 'put', 'head', 'post', 'delete' ]
  allowed_origins:
    description:
      - A list of one or more origins you want customers to be able to access the bucket from. This can contain at most one * wild character.
      required: true
      default: null
  expose_headers:
    description:
      - A list of one or more headers in the response that you want customers to be able to access from their applications (for example, from a JavaScript XMLHttpRequest object).
      required: false
      default: null
  state:
    description:
      - Create or remove the CORS rule
    required: false
    default: null
    choices: [ 'present', 'absent' ]
  max_age_seconds:
    description:
      - Time in seconds that the browser should cache the pre-flight response for the specified resource.
    required: false
    default: null

extends_documentation_fragment: aws
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.



'''

try:
    import boto3
    import botocore
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

def create_cors_rule_dict(module):

    cors_rule_dict = {}
    cors_rule_dict['AllowedHeaders'] = module.params.get('allowed_headers')
    cors_rule_dict['AllowedMethods'] = module.params.get('allowed_methods')
    cors_rule_dict['AllowedOrigins'] = module.params.get('allowed_origins')
    cors_rule_dict['ExposeHeaders'] = module.params.get('expose_headers')
    cors_rule_dict['MaxAgeSeconds'] = module.params.get('max_age_seconds')



def create_cors_rule(connection, module):

    bucket_name = module.params.get('name')

    # Get bucket current CORS rules
    bucket_cors = connection.BucketCors(bucket_name)

    rule = create_cors_rule_dict(module)

    print bucket_cors


def destroy_cors_rule(connection, module):


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True),
            allowed_headers=dict(default=None, required=False, type='list'),
            allowed_methods=dict(default=None, required=True, type='list', choices=['get', 'put', 'head', 'post', 'delete']),
            allowed_origins=dict(default=None, required=True, type='list'),
            expose_headers=dict(default=None, required=False, type='list'),
            state=dict(default='present', choices=['present', 'absent']),
            max_age_seconds=dict(default=None, type='int'),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=HAS_BOTO3)

    if region:
        try:
            connection = boto3_conn(module, conn_type='resource', resource='s3', region=region, endpoint=ec2_url, **aws_connect_kwargs)
        except botocore.exceptions.NoCredentialsError as e:
            module.fail_json(msg=e.message)
    else:
        module.fail_json(msg="region must be specified")

    state = module.params.get("state")

    if state == 'present':
        create_cors_rule(connection, module)
    elif state == 'absent':
        destroy_cors_rule(connection, module)


from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()