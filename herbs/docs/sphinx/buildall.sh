REMOTE_FOLDER="/home/scidam/webapps/herbdocs"

echo "Compiling Russian version of docs..."
cd ru
make clean
make latexpdf
cp -f build/latex/herbarium.pdf source/files/herbarium.pdf
make html

echo "Compiling English version of docs..."
cd ..
cd en
make clean
make latexpdf
cp -f build/latex/herbarium.pdf source/files/herbarium.pdf
make html
echo "Russian docs compiled successfully... Copying it to server..."


ssh myremote "mkdir -p $REMOTE_FOLDER/en"
scp -r ./build/html/* myremote:$REMOTE_FOLDER/en

cd ..
cd ru
ssh myremote "mkdir -p $REMOTE_FOLDER/ru"
scp -r ./build/html/* myremote:$REMOTE_FOLDER/ru

