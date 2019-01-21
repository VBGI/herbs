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


if [ -z "$(ls -A $homedir/output)" ]; then

    echo "Mounting output directory"
    sshfs kislov@jino:./domains/herbstatic.botsad.ru/snapshots $homedir/output

    echo "Mounting local source directory"
    sudo mount -t cifs "//192.168.1.11/exchange/Herbarium_" $homedir/source/local -o username=dmitry,workgroup=123,ro,password=123

    echo "Mounting remote source directory"
    sshfs scidam@myremote:/home/scidam/tmp/herbsnapshots $homedir/source/remote

    rm $homedir/herbimages.txt
    wget -P $homedir  herbstatic.botsad.ru/herbimages.txt
    cp $homedir/herbimages.txt $homedir/source/remote/herbimages.txt

    eval "$(pyenv init -)" && pyenv shell django && python $homedir/process_images.py

    echo "Wait for a moment..."
    sleep 1m

    sudo umount $homedir/output
    sudo umount $homedir/source/remote
    sudo umount $homedir/source/local

    echo "Everything is unmounted... Exiting... "

else
   echo "One or more directories aren't empty. Exiting..."
fi

