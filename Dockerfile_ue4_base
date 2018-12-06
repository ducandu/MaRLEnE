# to build the initial UE4 Engine without any game
# available on docker hub as ducandu/ue4

FROM ubuntu:xenial

# the github access token to use to download the UE4 repo from Epic
ARG ue4_git_token=
ENV UE4_GIT_TOKEN=$ue4_git_token

# the UE4 branch to checkout
ARG ue4_branch=release
ENV UE4_BRANCH=$ue4_branch

RUN apt-get update -y && apt-get install -y --no-install-recommends tzdata shared-mime-info libnss3 libxss1 libasound2 python3 python3-dev python3-pip sudo vim git mono-reference-assemblies-4.0 mono-devel mono-xbuild mono-mcs mono-dmcs libmono-system-data-datasetextensions4.0-cil libmono-system-web-extensions4.0-cil libmono-system-management4.0-cil libmono-system-xml-linq4.0-cil libmono-microsoft-build-tasks-v4.0-4.0-cil cmake dos2unix clang-5.0 clang-3.8 libqt4-dev git build-essential ca-certificates pkg-config bash-completion
RUN apt-get install -y python3-setuptools --upgrade
RUN apt-get install -y llvm
RUN apt-get install -y sed
RUN pip3 install numpy msgpack msgpack-numpy pydevd
# add some ue4 user (UE4 does not allow building with root)
RUN adduser --disabled-password --home /home/ue4 --shell /bin/bash ue4 && usermod -a -G sudo ue4

# change to new user
USER ue4
WORKDIR /home/ue4

# git all needed repos
RUN git clone https://${UE4_GIT_TOKEN}@github.com/EpicGames/UnrealEngine.git
WORKDIR UnrealEngine
# checkout the correct branch from UE4 (default: release)
RUN git checkout ${UE4_BRANCH}
RUN ./Setup.sh
RUN ./GenerateProjectFiles.sh -engine

RUN make

CMD ["bash"]

