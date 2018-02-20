#!/bin/sh

echo "init build (from scratch)"
echo "GAME=$GAME"
echo "UE4PYTHON_TAG=$UE4PYTHON_TAG"

cd

mkdir -p UnrealEngine/${GAME}/Plugins

# git all needed repos
# and copy the example game and the two plugins into UnrealEngine
git clone https://github.com/ducandu/marlene.git
cp -r marlene/examples/UE4Games/${GAME} UnrealEngine/.
cp -r marlene/Plugins/MaRLEnE UnrealEngine/${GAME}/Plugins/.

git clone https://github.com/20tab/UnrealEnginePython.git
cd UnrealEnginePython
git checkout tags/${UE4PYTHON_TAG}
cd ../
cp -r UnrealEnginePython UnrealEngine/${GAME}/Plugins/.

