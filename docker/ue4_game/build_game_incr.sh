#!/bin/sh

echo "GAME=$GAME"

cd /home/ue4/marlene
git pull
cd ../UnrealEnginePython
git pull

# copy (update; only newer files) the example game and the two plugins into UnrealEngine
cd
cp -r -u marlene/examples/UE4Games/${GAME} UnrealEngine/.
cp -r -u marlene/Plugins/MaRLEnE UnrealEngine/${GAME}/Plugins/.
cp -r -u UnrealEnginePython UnrealEngine/${GAME}/Plugins/.

