#!/bin/bash
# Shell install script for FlashCard
# Creates a virtual environment 'flash_cards', activates it, and installs requirements

ENV_NAME="flash_cards"
python3 -m venv $ENV_NAME
source $ENV_NAME/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "Setup complete."
