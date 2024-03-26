#!/usr/bin/env bash

DEVICE=/dev/ttyUSB0

rshell --port $DEVICE --quiet rm -r /pyboard/*

ampy --port $DEVICE put boot/boot.py /boot.py
ampy --port $DEVICE put boot/main.py /main.py

echo Done!
