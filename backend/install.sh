#!/bin/bash
# install.sh
pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
pip uninstall opencv-python -y
pip install opencv-python-headless
