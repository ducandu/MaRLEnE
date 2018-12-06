#!/usr/bin/env bash
add-apt-repository -y universe
apt update
sudo apt install git sudo shared-mime-info python3 python3-dev tzdata build-essential mono-mcs mono-devel mono-xbuild mono-dmcs mono-reference-assemblies-4.0 libmono-system-data-datasetextensions4.0-cil libmono-system-web-extensions4.0-cil libmono-system-management4.0-cil libmono-system-xml-linq4.0-cil cmake dos2unix clang-3.8 libfreetype6-dev libgtk-3-dev libmono-microsoft-build-tasks-v4.0-4.0-cil xdg-user-dirs -y
cd /vagrant/UnrealEngine

# clone project from github into a (new or empty) directory
mkdir -p $2
# clean up new directory before we can clone
rm -rf $2/*
git clone $1 $2

sudo apt install libnss3 libxss1 libasound2 -y

# do the build
/vagrant/UnrealEngine/Engine/Build/BatchFiles/RunUAT.sh BuildCookRun -project=$2 -nop4 -build -cook -compressed -stage -platform=Linux -clientconfig=Development -pak -archive -archivedirectory=$2"/Build" -utf8output

