#!/usr/bin/bash

# Install ansible and other necessary packages
yum install mlocate git PyYAML libyaml python-babel python-crypto python-ecdsa python-httplib2 python-jinja2 python-keyczar python-markupsafe python-paramiko python-pyasn1 python-six sshpass python-boto python-netaddr

mkdir -p /opt/codebase

cd /opt

git clone git://github.com/ansible/ansible.git --recursive

cd ansible

source ./hacking/env-setup



# Copy private key so Ansible can access itself
#cp /vagrant/.vagrant/machines/default/virtualbox/private_key /home/vagrant/.ssh/id_rsa

# Correct the ownership of the private key
#chown vagrant:vagrant /home/vagrant/.ssh/id_rsa

# Disable Ansible host key checking
#sed -i 's/#host_key_checking = False/host_key_checking = False/g' /etc/ansible/ansible.cfg

# Run the playbook to configure everything else
#su vagrant -c 'ansible-playbook /vagrant/.vagrant_provisioning/deploy_role.yml -i /vagrant/.vagrant_provisioning/inventories/local --extra-vars "role=ansible user=vagrant"'
