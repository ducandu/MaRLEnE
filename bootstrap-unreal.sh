#!/usr/bin/env bash

# start the cooked game without display (-NullRHI) and without sound (-nosound)

echo "
[Unit]
Description=$1 Service

[Service]
ExecStart=/vagrant/$1/Build/LinuxNoEditor/$1.sh -NullRHI -nosound
RestartSec=5s
Restart=always
User=ubuntu

[Install]
WantedBy=multi-user.target" > $1.service
mv $1.service /etc/systemd/system/$1.service
systemctl enable $1.service
systemctl start $1.service

