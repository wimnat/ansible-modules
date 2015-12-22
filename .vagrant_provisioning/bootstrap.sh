#!/usr/bin/bash

# Create .ssh folder
sudo mkdir /root/.ssh

# Copy private key
sudo cp /opt/codebase/ansible-modules/id_rsa_wimnat_201509 /root/.ssh/id_rsa

# Ownership and permission of key
sudo chown root:root /root/.ssh/id_rsa
sudo chmod 600 /root/.ssh/id_rsa

# Install git
sudo yum -y install git

# Add SSH known hosts
sudo sh -c 'ssh-keyscan bitbucket.org >> /root/.ssh/known_hosts'
sudo sh -c 'ssh-keyscan github.com >> /root/.ssh/known_hosts'

# Get scripts repo
cd /opt/codebase
sudo git clone git@bitbucket.org:wimnat/scripts.git

# Run setup script
sudo /bin/bash /opt/codebase/scripts/ansible_on_centos7.sh

