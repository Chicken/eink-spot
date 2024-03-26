#!/usr/bin/env bash

DEVICE=/dev/ttyUSB0

./upload.sh

echo Running...
pyboard --device $DEVICE -c "import src.main"
