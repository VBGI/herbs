#!/bin/bash

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"


homedir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Herbarium images conversion utility"

sudo umount $homedir/source/local
sudo umount $homedir/source/remote
sudo umount $homedir/output

sleep 10

mkdir -p "$homedir/source/local"
mkdir -p "$homedir/source/remote"


echo "Mounting output directory"
sshfs scidam@myremote:/home/scidam/webapps/herbviewer/snapshots $homedir/output


echo "Mounting local source directory"
sudo mount -t cifs "//fileserver/exchange/Herbarium_" $homedir/source/local -o username=dmitry,workgroup=123,ro,password=123

echo "Mounting remote source directory"
sshfs scidam@myremote:/home/scidam/tmp/herbsnapshots $homedir/source/remote

eval "$(pyenv init -)" && pyenv shell django && python $homedir/process_images.py



echo "I am sleeping now... wait a moment"
sleep 1m


sudo umount $homedir/output
sudo umount $homedir/source/remote
sudo umount $homedir/source/local

echo "Everything is unmounted... Exiting... "


