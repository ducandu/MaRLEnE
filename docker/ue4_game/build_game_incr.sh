#!/bin/sh

echo "incremental build"
echo "GAME=$GAME"
echo "UE4PYTHON_TAG=$UE4PYTHON_TAG"

cd /home/ue4/marlene
git pull origin master
cd ../UnrealEnginePython
git checkout tags/${UE4PYTHON_TAG}
git pull

# copy (update; only newer files) the example game and the two plugins into UnrealEngine
cd
cp -r -u marlene/examples/UE4Games/${GAME} UnrealEngine/.
cp -r -u marlene/Plugins/MaRLEnE UnrealEngine/${GAME}/Plugins/.
cp -r -u UnrealEnginePython UnrealEngine/${GAME}/Plugins/.

