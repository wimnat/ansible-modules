#!/usr/bin/python
# This script is released under the GNU General Public License, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: ec2_win_password 
short_description: Retrieve the password of an ec2 Windows instance
description:
    - Retrieves the password hash from an ec2 Windows instance, decrypts it and displays the result. This module has a dependency on python-boto and m2crypto.
version_added: "0.1"
options:
  instance_id:
    description:
      - The EC2 resource id. 
    required: true
    default: null 
    aliases: []
  region:
    description:
      - region in which the resource exists. 
    required: false
    default: null
    aliases: ['aws_region', 'ec2_region']
  state:
    private_key_path:
      - The path to the private key required to decrypt the password. E.g. /root/.ssh/private_key
    required: true
    default: null
    aliases: []

author: Rob White
'''

EXAMPLES = '''
# Basic example showing how to retrieve the instance password
tasks:
- name: Retrieve password
  ec2_win_password: instance_id=i-XXXXXXXX private_key_path=/path/to/private_key

'''

#import sys
#import time
import base64
import os.path

try:
    import boto.ec2
except ImportError:
    print "failed=True msg='boto required for this module'"
    sys.exit(1)

try:
    from M2Crypto import RSA
except ImportError:
    print "failed=True msg='m2crypto required for this module'"
    sys.exit(1)

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
            instance_id = dict(required=True),
            private_key_path = dict(required=True),
        )
    )
    module = AnsibleModule(argument_spec=argument_spec)

    instance_id = module.params.get('instance_id')
    private_key_path = module.params.get('private_key_path')
  
    ec2 = ec2_connect(module)
    
    # Check that the provided private key exists
    if not os.path.isfile(private_key_path):
        module.fail_json(msg="private_key_path does not exist")
    else:
        try:
            # Load the private key
            private_key = RSA.load_key(private_key_path)
        except RSA.RSAError:
            module.fail_json(msg="not a valid RSA key")

    try:
        encrypted_password = ec2.get_password_data(instance_id, False)
    except boto.exception.EC2ResponseError:
        module.fail_json(msg="ec2 response error. Invalid instance-id?")

    # Query for the instance id and then decrypt it
    try:
        password = private_key.private_decrypt(base64.decodestring(encrypted_password), RSA.pkcs1_padding)
    except RSA.RSAError:
        module.fail_json(msg="An RSA error occurred. The private key is probably incorrect.")
    except:
        module.fail_json(msg="An unknown error occurred")

    module.exit_json(changed=True, password=password)

    sys.exit(0)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
