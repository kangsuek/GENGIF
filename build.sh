#!/usr/bin/env bash
# exit on error
set -o errexit

# Install system dependencies for Pillow and rembg
apt-get update
apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff-dev \
    libwebp-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    tcl-dev \
    tk-dev

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
