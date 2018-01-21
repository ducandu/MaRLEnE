# to update and incrementally build/cook a game
# creates a new image based on the game's init image to allow for a fast incremental build/cook
ARG base_container=ue4_alieninvaders

FROM ducandu/$base_container

USER ue4
WORKDIR /home/ue4

# update our repos
WORKDIR marlene
RUN git pull
WORKDIR UnrealEnginePython
RUN git pull

# copy (update; only newer files) the example game and the two plugins into UnrealEngine
WORKDIR /home/ue4
RUN cp -r -u marlene/examples/UE4Games/${GAME} UnrealEngine/.
RUN cp -r -u marlene/Plugins/MaRLEnE UnrealEngine/${GAME}/Plugins/.
RUN cp -r -u UnrealEnginePython UnrealEngine/${GAME}/Plugins/.

WORKDIR UnrealEngine

# update necessary scripts from the plugin to the game's content folder
RUN cp -u ${GAME}/Plugins/MaRLEnE/Scripts/* ${GAME}/Content/Scripts/.

# incrementally build and cook the game
RUN Engine/Build/BatchFiles/RunUAT.sh BuildCookRun -project=${GAME}/${GAME}.uproject -nop4 -build -cook -compressed -stage -platform=Linux -clientconfig=Development -pak -archive -archivedirectory="${GAME}/Build" -utf8output

CMD ["bash"]
