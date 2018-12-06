# to build a final game image that only contains the cooked game executable
# and support for openGL applications (observable from outside the container via an xwindow server)
ARG base_img=ducandu/ue4_alien_invaders:build

# the base image to copy from
FROM $base_img AS game_img


FROM ubuntu:xenial

ARG game=AlienInvaders
#ENV DEFAULT_DOCKCROSS_IMAGE thewtex/opengl

# - install minimal python tools to be able to run plugin UnrealEnginePython
# - install xwindow server (to look at graphics inside the container)
# - install
RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y git libgl1-mesa-dri mesa-utils menu net-tools openbox python-pip sudo supervisor python3 python3-dev python3-pip python3-setuptools vim tint2 x11-xserver-utils x11vnc xinit xserver-xorg-video-dummy xserver-xorg-input-void websockify
RUN rm -f /usr/share/applications/x11vnc.desktop
RUN apt-get install -y wget
RUN apt-get remove -y python-pip && wget https://bootstrap.pypa.io/get-pip.py && python get-pip.py && pip install supervisor-stdout
RUN pip3 install numpy msgpack msgpack-numpy pydevd
RUN apt-get install -y gdb
RUN apt-get -y clean

COPY docker/ue4_game_exec/etc/skel/.xinitrc /etc/skel/.xinitrc

RUN useradd -m -s /bin/bash ue4
RUN echo "user ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/ue4

USER ue4
RUN cp /etc/skel/.xinitrc /home/ue4/

USER root
RUN git clone https://github.com/kanaka/noVNC.git /opt/noVNC && \
  cd /opt/noVNC && \
  git checkout 6a90803feb124791960e3962e328aa3cfb729aeb && \
  ln -s vnc_auto.html index.html

# noVNC (http server) is on 6080, and the VNC server is on 5900, and the UE4 Game on 6025
EXPOSE 6080 5900 6025

COPY docker/ue4_game_exec/etc /etc
COPY docker/ue4_game_exec/usr /usr

ENV DISPLAY :0

# change to new user
USER ue4
WORKDIR /home/ue4

RUN mkdir -p Games
WORKDIR Games
ENV DISPLAY :0
ENV GAME=$game
RUN echo "GAME=${GAME}"

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

USER root
WORKDIR /root

# run the game through the supervisor
ENV APP "/home/ue4/Games/${GAME}.sh -nosound -opengl3"

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]

