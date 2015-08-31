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
module: sqs_queue
short_description: Manage AWS SQS Queues
description:
  - Manage AWS SQS Queues
version_added: "1.9"
author: Rob White <wimnat [at] gmail.com>
options:
  state:
    description:
      - create or destroy a queue
    default: present
    choices: ['present', 'absent']
  name:
    description:
      - name of the queue
    required: true
  timeout:
    description:
      - default visibility timeout for all messages written in the queue. This can be overridden on a per-message basis.
    required: false
    default: 30
extends_documentation_fragment: aws
'''

EXAMPLES = '''
- sqs_queue:
    name: examplequeue
    timeout: 60
    state: present
    
'''

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

try:
    import boto.sqs
    from boto.exception import BotoServerError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False


def create_sqs_queue(connection, module):
    
    name = module.params.get('name')
    timeout = module.params.get('timeout')
    changed = False
    
    # Look up queue to see if it exists
    try:
        q = connection.lookup(name)
    except BotoServerError, e:
        module.fail_json(msg=str(e))
    
    if q is None: 
        try:
            q = connection.create_queue(name, timeout)
            changed = True
        except BotoServerError, e:
            module.fail_json(msg=str(e))
    else:
        try:
            if q.get_timeout() != timeout:
                q.set_timeout(timeout)
                changed = True
        except BotoServerError, e:
            module.fail_json(msg=str(e))
        
    module.exit_json(changed=changed, name=q.name, id=q.id, arn=q.arn, url=q.url, visibility_timeout=str(q.get_timeout()))


def delete_sqs_queue(connection, module):
    
    name = module.params.get('name')
    changed = False
    
    # Look up queue to see if it exists
    try:
        q = connection.lookup(name)
    except BotoServerError, e:
        module.fail_json(msg=str(e))
    
    if q is not None: 
        try:
            connection.delete_queue(q)
            changed = True
        except BotoServerError, e:
            module.fail_json(msg=str(e))
        
    module.exit_json(changed=changed)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True, type='str'),
            timeout=dict(type='int', default='30'),
            state=dict(default='present', choices=['present', 'absent'])
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)
    
    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)

    try:
        connection = connect_to_aws(boto.sqs, region, **aws_connect_params)
    except (boto.exception.NoAuthHandlerFound, StandardError), e:
        module.fail_json(msg=str(e))

    state = module.params.get('state')

    if state == 'present':
        create_sqs_queue(connection, module)
    elif state == 'absent':
        delete_sqs_queue(connection, module)

main()
