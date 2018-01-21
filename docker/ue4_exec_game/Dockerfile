ARG base_container=base_container
FROM ducandu/ue4_game AS game
RUN echo " "


# new container based on Ubuntu
FROM ubuntu:xenial

# install minimal python tools to be able to run plugin UnrealEnginePython
RUN apt-get update -y && apt-get install -y --no-install-recommends python3 python3-dev python3-pip python3-setuptools
RUN pip3 install numpy msgpack msgpack-numpy pydevd

# add the game user
RUN adduser --disabled-password --home /home/ue4 --shell /bin/bash ue4 && usermod -a -G sudo ue4
# change to new user
USER ue4
WORKDIR /home/ue4
RUN mkdir -p Games/AlienInvaders
WORKDIR Games/AlienInvaders

# just copy the cooked game
COPY --from=game --chown=ue4:ue4 /home/ue4/UnrealEngine/AlienInvaders/Build/LinuxNoEditor ./
# and the python scripts
RUN mkdir -p AlienInvaders/Content/Scripts
COPY --from=game --chown=ue4:ue4 /home/ue4/UnrealEngine/AlienInvaders/Content/Scripts AlienInvaders/Content/Scripts/

#USER root
#RUN chmod -R 0777 /home/ue4/Games/AlienInvaders
#USER ue4

# TODO: add PYTHONPATH pointing to Games/.../Content/Scripts to env

# start the game automatically when running this container
# CMD ["/home/ue4/Games/AlienInvaders/AlienInvaders.sh -NullRHI -nosound"]
CMD ["bash"]

