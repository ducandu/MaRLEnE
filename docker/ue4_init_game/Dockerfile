# to build a initial game on top of the basic (engine) ducandu/ue4 container

# - use docker build --build-arg game=AlienInvaders to build this image
# `docker build --build-arg game=AlienInvaders -l ducandu/ue4_[some_game_name] .`

FROM ducandu/ue4

USER ue4
WORKDIR /home/ue4

# default game; override this via `--build-arg game=` on `docker build` command line
ARG game=AlienInvaders
ENV GAME=$game

# git all needed repos
RUN git clone https://github.com/ducandu/marlene.git
RUN git clone https://github.com/20tab/UnrealEnginePython.git
RUN mkdir -p UnrealEngine/${GAME}/Plugins
# copy the example game and the two plugins into UnrealEngine
RUN cp -r marlene/examples/UE4Games/${GAME} UnrealEngine/.
RUN cp -r marlene/Plugins/MaRLEnE UnrealEngine/${GAME}/Plugins/.
RUN cp -r UnrealEnginePython UnrealEngine/${GAME}/Plugins/.

WORKDIR UnrealEngine

## Modify the UnrealEnginePython build cs file to add the python lib and include paths
# not necessary as ubuntu is covered by the default values in UEPython build cs
#RUN sed -i 's/\/usr\/local\/include\/python3.6//' AlienInvaders/Plugins/UnrealEnginePython/Source/UnrealEnginePython/UnrealEnginePython.Build.cs

# - copy necessary scripts from the plugin to the game's content folder
RUN mkdir -p ${GAME}/Content/Scripts/ && cp ${GAME}/Plugins/MaRLEnE/Scripts/* ${GAME}/Content/Scripts/.

# initial build and cook of the game
RUN Engine/Build/BatchFiles/RunUAT.sh BuildCookRun -project=${GAME}/${GAME}.uproject -nop4 -build -cook -compressed -stage -platform=Linux -clientconfig=Development -pak -archive -archivedirectory="${GAME}/Build" -utf8output

CMD ["bash"]
