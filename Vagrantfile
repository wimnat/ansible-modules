# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure(2) do |config|

  #  ENV["VAGRANT_DETECTED_OS"] = ENV["VAGRANT_DETECTED_OS"].to_s + " cygwin"
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://atlas.hashicorp.com/search.
  config.vm.box = "dummybox-aws"

  # Disable automatic box update checking. If you disable this, then
  # boxes will only be checked for updates when the user runs
  # `vagrant box outdated`. This is not recommended.
  # config.vm.box_check_update = false

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  # config.vm.network "forwarded_port", guest: 80, host: 8080

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  # config.vm.network "private_network", ip: "192.168.33.10"

  # Create a public network, which generally matched to bridged network.
  # Bridged networks make the machine appear as another physical device on
  # your network.
  # config.vm.network "public_network"

  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  # config.vm.synced_folder "../data", "/vagrant_data"

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:
  #
  # config.vm.provider "virtualbox" do |vb|
  #   # Display the VirtualBox GUI when booting the machine
  #   vb.gui = true
  #
  #   # Customize the amount of memory on the VM:
  #   vb.memory = "1024"
  # end
  #
  # View the documentation for the provider you are using for more
  # information on available options.

  # Define a Vagrant Push strategy for pushing to Atlas. Other push strategies
  # such as FTP and Heroku are also available. See the documentation at
  # https://docs.vagrantup.com/v2/push/atlas.html for more information.
  # config.push.define "atlas" do |push|
  #   push.app = "YOUR_ATLAS_USERNAME/YOUR_APPLICATION_NAME"
  # end

  # Enable provisioning with a shell script. Additional provisioners such as
  # Puppet, Chef, Ansible, Salt, and Docker are also available. Please see the
  # documentation for more information about their specific syntax and use.
  # config.vm.provision "shell", inline: <<-SHELL
  #   sudo apt-get update
  #   sudo apt-get install -y apache2
  # SHELL
  config.vm.provision :shell, path: ".vagrant_provisioning/bootstrap.sh"

  config.vm.synced_folder ".", "/opt/codebase/ansible-modules", type: "rsync", rsync__exclude: [".git/", ".idea/"]
  config.vm.hostname = "stagingbox"

  config.vm.provider :aws do |aws, override|

    # AWS Settings
    aws.access_key_id = ENV['AWS_ACCESS_KEY']
    aws.secret_access_key = ENV['AWS_SECRET_KEY']
    aws.region = "ap-southeast-2"

    aws.associate_public_ip = "true"
    aws.iam_instance_profile_name = "iam-ansible"

    aws.tags = {
      'Name' => 'Vagrant-Ansible-Modules',
    }

    # Override Settings
    #override.ssh.username = "ec2-user"
    override.ssh.username = "centos"
    override.ssh.private_key_path = "id_rsa_wimnat_201509"

    # Oregon
    aws.region_config "us-west-2" do |region|
      region.ami = 'ami-f0091d91'
      # CentOS 7 AMI - ami-d440a6e7
      region.instance_type = 't2.micro'
      region.keypair_name = ENV['AWS_KEY_NAME']
      region.security_groups = "sec-ansible"
    end

    # Sydney
    aws.region_config "ap-southeast-2" do |region|
      # CentOS 7 AMI
      region.ami = 'ami-d38dc6e9'
      region.instance_type = 't2.micro'
      region.keypair_name = ENV['AWS_KEY_NAME']
      region.security_groups = "sg-92e6d9f7"
      region.subnet_id = "subnet-2d81ff48"
    end

  end

end
