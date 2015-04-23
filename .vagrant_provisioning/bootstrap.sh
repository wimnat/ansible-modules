#!/usr/bin/bash

# Install ansible and other necessary packages
yum -y install ansible sshpass python-boto python-netaddr git

# Copy private key so Ansible can access itself
cp /vagrant/.vagrant/machines/default/virtualbox/private_key /home/vagrant/.ssh/id_rsa

# Correct the ownership of the private key
chown vagrant:vagrant /home/vagrant/.ssh/id_rsa

# Disable Ansible host key checking
sed -i 's/#host_key_checking = False/host_key_checking = False/g' /etc/ansible/ansible.cfg

# Run the playbook to configure everything else
su vagrant -c 'ansible-playbook /vagrant/.vagrant_provisioning/deploy_role.yml -i /vagrant/.vagrant_provisioning/inventories/local --extra-vars "role=ansible user=vagrant"'
