

sshfs scidam@myremote:/home/scidam/webapps/herbviewer/snapshots ./output

sudo mount -t cifs "//fileserver/exchange/Гербарий Таня" source -o username=dmitry,workgroup=123,ro,password=123

python process_images.py

sudo umount ./output
sudo umount ./source

