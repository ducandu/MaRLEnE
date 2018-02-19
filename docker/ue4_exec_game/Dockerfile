# to build a final game image that only contains the cooked game executable

ARG base_img=ducandu/ue4_alien_invaders

# the base image to copy from
FROM $base_img AS game_img

# new container based on Ubuntu
FROM ubuntu:xenial

ARG game=AlienInvaders

# install minimal python tools to be able to run plugin UnrealEnginePython
RUN apt-get update -y && apt-get install -y --no-install-recommends python3 python3-dev python3-pip python3-setuptools
RUN pip3 install numpy msgpack msgpack-numpy pydevd

# add the game user
RUN adduser --disabled-password --home /home/ue4 --shell /bin/bash ue4 && usermod -a -G sudo ue4
# change to new user
USER ue4
WORKDIR /home/ue4

ENV GAME=$game
RUN echo "GAME=${GAME}"

RUN mkdir -p Games
WORKDIR Games

# just copy the cooked game
COPY --from=game_img --chown=ue4:ue4 /home/ue4/UnrealEngine/${GAME}/Build/LinuxNoEditor ./
# and the python scripts
RUN mkdir -p AlienInvaders/Content/Scripts
COPY --from=game_img --chown=ue4:ue4 /home/ue4/UnrealEngine/${GAME}/Content/Scripts ${GAME}/Content/Scripts/

# add to PYTHONPATH: Games/[the GAME]/Content/Scripts
ENV PYTHONPATH=/home/ue4/Games/${GAME}/Content/Scripts

# start the game automatically when running this container
CMD /home/ue4/Games/${GAME}.sh -NullRHI -nosound

# run this container (detached) and with port 6025 open for listening with (no need for --network option!!):
# `docker run -it -d --name [e.g aliens] -p 6025:6025 ducandu/ue4_[game]_final`
# login to this container via
# `docker exec -ti [container name] bash`
