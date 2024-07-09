#!/usr/bin/bash

# Copy to /opt

sudo mkdir -pv /opt/FallbackImager
sudo cp -rav dist-lin/* /opt/FallbackImager
sudo cp -av fallbackimager.desktop /usr/share/applications
