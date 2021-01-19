# See here for image contents: https://github.com/microsoft/vscode-dev-containers/tree/v0.154.2/containers/ubuntu/.devcontainer/base.Dockerfile

# [Choice] Ubuntu version: bionic, focal
ARG VARIANT="focal"
FROM mcr.microsoft.com/vscode/devcontainers/base:0-${VARIANT}

RUN echo "deb http://archive.ubuntu.com/ubuntu bionic main universe" >> /etc/apt/sources.list

RUN apt-get update -y && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends openjdk-11-jdk unzip wget git ssh tar gzip ca-certificates libusb-1.0 libpng16-16 libgtk2.0-0 libwebkitgtk-1.0-0 libwebkitgtk-3.0-0 && \
    apt-get clean && \
	rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Garmin Connect IQ SDK Manager
RUN echo "Downloading Connect IQ SDK Manager:" && \
    cd /opt && \
    wget -q https://developer.garmin.com/downloads/connect-iq/sdk-manager/connectiq-sdk-manager-linux.zip -O sdk-manager.zip && \
    unzip sdk-manager.zip -d sdk-manager && \
    rm -f sdk-manager.zip

# Fix missing libpng12 (monkeydo)
RUN ln -s /usr/lib/x86_64-linux-gnu/libpng16.so.16 /usr/lib/x86_64-linux-gnu/libpng12.so.0

ENV PATH ${PATH}:/opt/sdk-manager/bin
