#!/bin/bash

python3 -m venv .venv

. ./.venv/bin/activate

pip install -r requirements.txt

deactivate

SCRIPT_PATH=$( cd -- $(dirname $0) >/dev/null 2>&1 ; pwd -P )

sudo ln -s "${SCRIPT_PATH}/dasExporter.service" /etc/systemd/system/dasExporter.service

sudo systemctl daemon-reload
sudo systemctl start dasExporter
sudo systemctl enable dasExporter
