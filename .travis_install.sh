#!/bin/bash

UBUNTU_XENIAL="deb http://archive.ubuntu.com/ubuntu xenial main"
DEBIAN_UNSTABLE="deb http://ftp.se.debian.org/debian/ sid main"

# https://bugs.launchpad.net/ubuntu/+source/dpkg/+bug/1730627
echo $UBUNTU_XENIAL | sudo tee /etc/apt/sources.list.d/ubuntu_xenial.list
sudo apt update
sudo apt install -o APT::Force-LoopBreak=1 dpkg libc6

echo $DEBIAN_UNSTABLE | sudo tee /etc/apt/sources.list.d/debian_unstable.list
sudo apt-get --allow-unauthenticated update
sudo apt install -y --allow-unauthenticated -t sid libclips libclips-dev

sudo pip install --upgrade pip
sudo pip install --upgrade setuptools
sudo pip install --upgrade pytest

pip install .
