# -*- mode: ruby -*-
# vi: set ft=ruby :
#
# vagrant up --provider=libvirt

Vagrant.configure("2") do |config|
  config.vm.box = "fedora/31-beta-cloud-base"
  config.vm.provision "shell", inline: "cd /vagrant; sudo ./setup-env.sh"
end
