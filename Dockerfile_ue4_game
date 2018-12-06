# to build a game on top of either a) the basic (engine) ducandu/ue4 container
# or b) a previously compiled/cooked game

# provide build-args:
# game=[the project's name, e.g. AlienInvaders (default)]
# base_img=[the base image to use: `ducandu/ue4` for initial build, or `ducandu/ue4_[some_game]:build` for a previously built game]

ARG base_img=ducandu/ue4

FROM $base_img

USER ue4
WORKDIR /home/ue4

# default game; override this via `--build-arg game=` on `docker build` command line
ARG base_img=ducandu/ue4
ENV BASE_IMG=$base_img
ARG game=AlienInvaders
ENV GAME=$game
ARG ue4python_tag=""
ENV UE4PYTHON_TAG=$ue4python_tag
ARG local=false
ENV BUILD_FROM_LOCAL=$local

RUN git config --global user.email "svenmika1977@gmail.com"
RUN git config --global user.name "sven1977"

COPY --chown=ue4:ue4 docker/ue4_game/build_game_init.sh .
COPY --chown=ue4:ue4 docker/ue4_game/build_game_incr.sh .
COPY --chown=ue4:ue4 docker/ue4_game/build_game_local.sh .

RUN dos2unix build_game_init.sh
RUN dos2unix build_game_incr.sh
RUN dos2unix build_game_local.sh

RUN chmod 0777 build_*.sh

# just in case if BUILD_FROM_LOCAL==true: copy local MaRLEnE plugin into container (no need to go to git all the time)
COPY --chown=ue4:ue4 Plugins/MaRLEnE local_marlene
COPY --chown=ue4:ue4 examples local_examples

# TODO: nix difference between these scripts: they should always try to pull from github (if doesn't exist, clone). Only if "local": Copy from local Marlene (plugin, scripts & example games) instead.
RUN if [ "${BUILD_FROM_LOCAL}" = "true" ] ; then /bin/sh ./build_game_local.sh ; elif [ "${BASE_IMG}" = "ducandu/ue4" ] ; then /bin/sh ./build_game_init.sh ; else /bin/sh ./build_game_incr.sh ; fi

WORKDIR UnrealEngine
## Modify the UnrealEnginePython build cs file to add the python lib and include paths
# not necessary as ubuntu is covered by the default values in UEPython build cs
#RUN sed -i 's/\/usr\/local\/include\/python3.6//' AlienInvaders/Plugins/UnrealEnginePython/Source/UnrealEnginePython/UnrealEnginePython.Build.cs

# TODO: Temporarily: copy fixed driver cpp file into container's UE4 source code
COPY --chown=ue4:ue4 docker/ue4_game/OpenGLDrv.cpp Engine/Source/Runtime/OpenGLDrv/Private/.

# - copy necessary scripts from the plugin to the game's content folder
RUN mkdir -p ${GAME}/Content/Scripts/
# force-copy (no -u flag), because some Scripts may exist in the examples/[some Game] folder of MaRLEnE with
# the same age as the scripts in MaRLEnE/Scripts/
RUN cp ${GAME}/Plugins/MaRLEnE/Scripts/* ${GAME}/Content/Scripts/.

# build and cook the game
RUN Engine/Build/BatchFiles/RunUAT.sh BuildCookRun -project=${GAME}/${GAME}.uproject -nop4 -build -cook -compressed -stage -platform=Linux -clientconfig=Development -pak -archive -archivedirectory="${GAME}/Build" -utf8output

CMD ["bash"]
