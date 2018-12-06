# to build a final game image that only contains the cooked game executable
# and support for openGL applications (observable from outside the container via an xwindow server)
ARG base_img=ducandu/ue4_alien_invaders:build

# the base image to copy from
FROM $base_img AS game_img

FROM ubuntu:xenial

ARG game=AlienInvaders
RUN apt-get update && apt-get install -y xvfb xserver-xorg gdb mesa-utils wget sudo python3 python3-dev python3-pip python3-setuptools vim
RUN pip3 install numpy msgpack msgpack-numpy pydevd
RUN apt-get -y clean

RUN useradd -m -s /bin/bash ue4
RUN echo "user ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/ue4

USER ue4

# noVNC (http server) is on 6080, and the VNC server is on 5900, and the UE4 Game on 6025
EXPOSE 6080 5900 6025

ENV DISPLAY :1.0
ENV GAME=$game
RUN echo "GAME=${GAME}"

WORKDIR /home/ue4

RUN mkdir -p Games

WORKDIR Games

# just copy the cooked game
COPY --from=game_img --chown=ue4:ue4 /home/ue4/UnrealEngine/${GAME}/Build/LinuxNoEditor ./
# and the python scripts
RUN mkdir -p AlienInvaders/Content/Scripts
COPY --from=game_img --chown=ue4:ue4 /home/ue4/UnrealEngine/${GAME}/Content/Scripts ${GAME}/Content/Scripts/

# add to PYTHONPATH: Games/[the GAME]/Content/Scripts
ENV PYTHONPATH=/home/ue4/Games/${GAME}/Content/Scripts

# setup mesa to use the correct openGL and GLSL (shader language) versions (UE4 does not support any openGL-3)
# FOR NOW: leave openGL 3 (4 doesn't seem to work with current UE4)
#ENV MESA_GLSL_VERSION_OVERRIDE=430
#ENV MESA_GL_VERSION_OVERRIDE=4.3
# also make sure we are using software rendering (no GPU)
ENV LIBGL_ALWAYS_SOFTWARE=true
# and use the correct mesa software gallium driver (llvm)
ENV GALLIUM_DRIVER="llvmpipe"

# run this container (detached) and with port 6025 open for listening with (no need for --network option!!):
# `docker run -it --name [e.g aliens] -p 6080:6080 -p 6025:6025 ducandu/ue4_[game]:exec`

CMD (Xvfb :1 -screen 0 1024x768x16 &> xvfb.log &) && (/home/ue4/Games/${GAME}.sh -nosound -opengl3)
