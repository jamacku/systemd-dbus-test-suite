# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "fedora/25-cloud-base"
  config.vm.provision "shell", inline: "cd /vagrant; sudo ./setup-env.sh"
end
