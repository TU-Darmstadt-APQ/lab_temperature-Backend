#!/usr/bin/bash

wget http://download.tinkerforge.com/tools/brickd/linux/brickd_linux_latest_armhf.deb
sudo dpkg -i brickd_linux_latest_armhf.deb

sudo apt-get install screen

sudo apt-get install python3-pip

sudo pip install pyserial

sudo pip install cbor2

sudo pip install cobs

sudo pip install tinkerforge

sudo pip install flask

sudo pip install wtforms

sudo pip install flask_wtf

echo "All libraries were successfully installed."