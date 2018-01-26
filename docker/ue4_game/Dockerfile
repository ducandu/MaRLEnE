# to build a game on top of either a) the basic (engine) ducandu/ue4 container
# or b) a previously compiled/cooked game

# provide build-args:
# game=[the project's name, e.g. AlienInvaders (default)]
# base_img=[the base image to use: `ue4` for initial build, or `ue4_alien` for an already built game]

ARG base_img=ue4

FROM ducandu/$base_img

USER ue4
WORKDIR /home/ue4

RUN echo " abc"

# default game; override this via `--build-arg game=` on `docker build` command line
ARG base_img=ue4
ENV BASE_IMG=$base_img
ARG game=AlienInvaders
ENV GAME=$game

COPY --chown=ue4:ue4 build_game_init.sh .
COPY --chown=ue4:ue4 build_game_incr.sh .
RUN dos2unix build_game_init.sh
RUN dos2unix build_game_incr.sh
RUN chmod 0777 build_game_init.sh && chmod 0777 build_game_incr.sh
RUN if [ "${BASE_IMG}" = "ue4" ] ; then /bin/sh ./build_game_init.sh ; else /bin/sh ./build_game_incr.sh ; fi

WORKDIR UnrealEngine
## Modify the UnrealEnginePython build cs file to add the python lib and include paths
# not necessary as ubuntu is covered by the default values in UEPython build cs
#RUN sed -i 's/\/usr\/local\/include\/python3.6//' AlienInvaders/Plugins/UnrealEnginePython/Source/UnrealEnginePython/UnrealEnginePython.Build.cs

# - copy necessary scripts from the plugin to the game's content folder
RUN mkdir -p ${GAME}/Content/Scripts/
RUN cp -u ${GAME}/Plugins/MaRLEnE/Scripts/* ${GAME}/Content/Scripts/.

# build and cook the game
RUN Engine/Build/BatchFiles/RunUAT.sh BuildCookRun -project=${GAME}/${GAME}.uproject -nop4 -build -cook -compressed -stage -platform=Linux -clientconfig=Development -pak -archive -archivedirectory="${GAME}/Build" -utf8output

CMD ["bash"]
