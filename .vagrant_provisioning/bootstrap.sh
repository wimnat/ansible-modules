#!/usr/bin/bash

# Install ansible and other necessary packages
yum -y install ansible sshpass python-boto python-netaddr git

# Copy private key so Ansible can access itself
cp /vagrant/.vagrant/machines/default/virtualbox/private_key /home/vagrant/.ssh/id_rsa

# Run the playbook to configure everything else
ansible-playbook /vagrant/.vagrant_provisioning/deploy_role.yml -i /vagrant/.vagrant_provisioning/inventories/local --extra-vars "role=ansible user=vagrant"
