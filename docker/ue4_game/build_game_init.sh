#!/bin/sh

echo "GAME=$GAME"

mkdir -p UnrealEngine/${GAME}/Plugins

# git all needed repos
# and copy the example game and the two plugins into UnrealEngine
git clone https://github.com/ducandu/marlene.git
cp -r marlene/examples/UE4Games/${GAME} UnrealEngine/.
cp -r marlene/Plugins/MaRLEnE UnrealEngine/${GAME}/Plugins/.

git clone https://github.com/20tab/UnrealEnginePython.git
cp -r UnrealEnginePython UnrealEngine/${GAME}/Plugins/.

