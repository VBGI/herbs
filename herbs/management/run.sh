#!/bin/bash

echo "Herbarium images conversion utility"

sudo umount ./source/local
sudo umount ./source/remote
sudo umount ./output

sleep 10

mkdir -p "./source/local"
mkdir -p "./source/remote"


echo "Mounting output directory"
sshfs scidam@myremote:/home/scidam/webapps/herbviewer/snapshots ./output


echo "Mounting local source directory"
sudo mount -t cifs "//fileserver/exchange/Herbarium_Tanya" source/local -o username=dmitry,workgroup=123,ro,password=123

echo "Mounting remote source directory"
sshfs scidam@myremote:/home/scidam/tmp/herbsnapshots ./source/remote


python process_images.py

echo "I am sleeping now... wait a moment"
sleep 1m


sudo umount ./output
sudo umount ./source/remote
sudo umount ./source/local

echo "Everything is unmounted... Exiting... "


