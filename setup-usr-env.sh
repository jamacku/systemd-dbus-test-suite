#!/bin/bash

set -e

[ "$EUID" = 0 ] && {
    echo 'Need to run as user'
    exit 1
}

pip_packages="avocado-framework"
echo "Installing pip packages: $pip_packages"
pip3 install --user "$pip_packages" >/dev/null 2>&1

