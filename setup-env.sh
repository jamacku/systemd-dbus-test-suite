#!/bin/bash

set -e

[ "$EUID" = 0 ] || {
    echo 'Need to run as root'
    exit 1
}

#packages=""
#echo "Installing packages: $packages"
#dnf install -y $packages >/dev/null 2>&1

pip_packages="pydbus"
echo "Installing pip packages: $pip_packages"
pip3 install "$pip_packages" >/dev/null 2>&1
