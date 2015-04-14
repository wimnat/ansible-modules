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
from _elementtree import ElementTree

DOCUMENTATION = '''
---
module: ec2_eni
short_description: Create and optionally attach an Elastic Network Interface (ENI) to an instance
description:
    - Create and optionally attach an Elastic Network Interface (ENI) to an instance
version_added: "1.9"
author: Mohammed Salih
options:
  instance_id:
    description:
      - Instance ID that you wish to attach ENI to 
    required: false
    default: null 
    aliases: []
  private_ip_address:
    description:
      - Private IP address.
    required: false
    default: null
    aliases: []
  subnet_id:
    description:
      - Subnet in which to create the ENI
    required: true
    default: null
    aliases: []
  description:
    description:
      - Optional description of the ENI
    required: false
    default: null
    aliases: []
  security_groups:
    description:
      - Comma separated list of one or more security groups. Only used when state=present.
    required: false
    default: null
    aliases: []
  state:
    description:
      - Create or delete ENI
    required: false
    default: present
  device_index:
    description:
      - The index of the device for the network interface attachment on the instance.
    required: false
    default: null
    aliases: []
extends_documentation_fragment: aws
requirements: [ "boto" ]
'''

EXAMPLES = '''
# Create and attach action.
- local_action: 
    module: ec2_eni
    instance: i-xxxxxxxx
    private_ip_address: 172.31.0.20
    subnet_id: subnet-xxxxxxxx

'''

import sys
import time
import xml

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

try:
    import boto.ec2
    from boto.exception import BotoServerError
except ImportError:
    print "failed=True msg='boto required for this module'"
    sys.exit(1)

def get_eni_info(interface):
    
    interface_info = {'id': interface.id,
                      'subnet_id': interface.subnet_id,
                      'vpc_id': interface.vpc_id,
                      'description': interface.description,
                      'owner_id': interface.owner_id,
                      'status': interface.status,
                      'mac_address': interface.mac_address,
                      'private_ip_address': interface.private_ip_address,
                      'source_dest_check': interface.source_dest_check,
                      'groups': dict((group.id, group.name) for group in interface.groups),
                      }
    
    if interface.attachment is not None:
        interface_info['attachment'] = {'attachment_id': interface.attachment.id,
                                        'instance_id': interface.attachment.instance_id,
                                        'device_index': interface.attachment.device_index,
                                        'status': interface.attachment.status,
                                        'attach_time': interface.attachment.attach_time,
                                        'delete_on_termination': interface.attachment.delete_on_termination,
                                        }
    
    return interface_info
    
    
def create_eni(connection, module):
    
    eni_id = module.params.get("eni_id")
    instance_id = module.params.get("instance_id")
    device_index = module.params.get("device_index")
    subnet_id = module.params.get('subnet_id')
    private_ip_address = module.params.get('private_ip_address')
    description = module.params.get('description')
    security_groups = module.params.get('security_groups')
    changed = False
    
    try:
        eni = connection.create_network_interface(subnet_id, private_ip_address, description, security_groups)
        changed = True
    except BotoServerError as ex:
        #module.fail_json(msg=str(e))
        template = "An exception of type {0} occured. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print message
        print ex.args[2]
        
        #tree = ElementTree.fromstring()
        
        root = xml.ElementTree.fromstring(ex.args[2])
        #e = xml.etree.ElementTree.parse(ex.args[2]).getroot()
        print root.response.errors.error.message
        
    module.exit_json(changed=changed, id=eni.id, subnet_id=eni.subnet_id)
    
def delete_eni(connection, module):
    
    try:
        eni_id = "" 
        eni = ec2.delete_network_interface(eni_id)
        changed = True
    except BotoServerError, e:
        module.fail_json(msg=str(e))
        

def list_eni(connection, module):
    
    interface_dict_array = []
    all_eni = connection.get_all_network_interfaces()
    
    for interface in all_eni:
        interface_dict_array.append(get_eni_info(interface))
        
    module.exit_json(changed=False, interfaces=interface_dict_array)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            eni_id = dict(),
            instance_id = dict(),
            private_ip_address = dict(),
            subnet_id = dict(),
            description = dict(),
            security_groups = dict(),           
            device_index = dict(),
            state=dict(default='present', choices=['present', 'absent', 'list'])
        )
    )
    
    module = AnsibleModule(argument_spec=argument_spec)
    
    region, ec2_url, aws_connect_params = get_aws_connection_info(module)
    
    try:
        connection = connect_to_aws(boto.ec2, region, **aws_connect_params)
    except (boto.exception.NoAuthHandlerFound, StandardError), e:
        module.fail_json(msg=str(e))

    state = module.params.get('state')

    if state == 'present':
        create_eni(connection, module)
    elif state == 'absent':
        delete_eni(connection, module)
    elif state == 'list':
        list_eni(connection, module)
        
    module.fail_json(msg="got to end")

    instance = module.params.get('instance')
    private_ip_address = module.params.get('private_ip_address')
    subnet_id = module.params.get('subnet_id')
    device_index = module.params.get('device_index')
    sg_group = module.params.get('sg_group')
    description = module.params.get('description')
    region = module.params.get('region')
    zone = module.params.get('zone')
    ec2_url = module.params.get('ec2_url')
    ec2_secret_key = module.params.get('ec2_secret_key')
    ec2_access_key = module.params.get('ec2_access_key')

    # allow eucarc environment variables to be used if ansible vars aren't set
    if not ec2_url and 'EC2_URL' in os.environ:
        ec2_url = os.environ['EC2_URL']
    if not ec2_secret_key and 'EC2_SECRET_KEY' in os.environ:
        ec2_secret_key = os.environ['EC2_SECRET_KEY']
    if not ec2_access_key and 'EC2_ACCESS_KEY' in os.environ:
        ec2_access_key = os.environ['EC2_ACCESS_KEY']
    
    # If we have a region specified, connect to its endpoint.
    if region: 
        try:
            ec2 = boto.ec2.connect_to_region(region, aws_access_key_id=ec2_access_key, aws_secret_access_key=ec2_secret_key)
        except boto.exception.NoAuthHandlerFound, e:
            module.fail_json(msg = str(e))
    # Otherwise, no region so we fallback to the old connection method
    else: 
        try:
            if ec2_url: # if we have an URL set, connect to the specified endpoint 
                ec2 = boto.connect_ec2_endpoint(ec2_url, ec2_access_key, ec2_secret_key)
            else: # otherwise it's Amazon.
                ec2 = boto.connect_ec2(ec2_access_key, ec2_secret_key)
        except boto.exception.NoAuthHandlerFound, e:
            module.fail_json(msg = str(e))

    # If no instance supplied, try ENI creation based on module parameters.
    sg_group = [sg_group]
    try:
        eni = ec2.create_network_interface(subnet_id, private_ip_address, description, sg_group)
        nicfilter = {"network-interface-id" : eni.id}
        while ec2.get_all_network_interfaces(nicfilter)[0].status != 'available':
            time.sleep(3)
    except boto.exception.BotoServerError, e:
        module.fail_json(msg = "%s: %s" % (e.error_code, e.error_message))

    # Attach the new ENI if instance is specified.

    if instance:
        reservation = ec2.get_all_instances(instance_ids=instance)
        inst = reservation[0].instances[0]
        zone = inst.placement
        try:
            attach = ec2.attach_network_interface(eni.id, inst.id, device_index)
            while ec2.get_all_network_interfaces(nicfilter)[0].status != 'in-use':
                time.sleep(3)
        except boto.exception.BotoServerError, e:
            module.fail_json(msg = "%s: %s" % (e.error_code, e.error_message))           
   

    print json.dumps({
        "eni_id": eni.id
    })
    sys.exit(0)

# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>

main()