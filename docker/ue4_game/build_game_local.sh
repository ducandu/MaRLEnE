#!/bin/sh

echo "local build (local MaRLEnE Plugin version; UE Python always from git!)"
echo "GAME=$GAME"
echo "UE4PYTHON_TAG=$UE4PYTHON_TAG"

cd

mkdir -p UnrealEngine/${GAME}/Plugins/MaRLEnE

# copy all needed files (from the local COPY)
# and copy the example game and the two plugins into UnrealEngine
cp -r local_examples/UE4Games/${GAME} UnrealEngine/.
cp -r local_marlene/* UnrealEngine/${GAME}/Plugins/MaRLEnE/.
#cp -r local_marlene/Plugins/ForceSoftwareRenderer UnrealEngine/${GAME}/Plugins/.

# then do the UE4 python plugin
cd
cd UnrealEnginePython
git fetch
if [ -z "${UE4PYTHON_TAG}" ] ; then git checkout master ; echo "no tag"; else git checkout tags/${UE4PYTHON_TAG} ; echo "tag"; fi
git pull

cd
cp -rf UnrealEnginePython UnrealEngine/${GAME}/Plugins/.

