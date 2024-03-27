#!/usr/bin/env bash

DEVICE=/dev/ttyUSB0

if [ "$MAIN_ONLY" != "true" ] && [ "$ONLY_MAIN" != "true" ]
then
    echo Removing old code...
    rshell --port $DEVICE --quiet rm -r /pyboard/src
fi
echo Adding new code...
if [ "$MAIN_ONLY" != "true" ] && [ "$ONLY_MAIN" != "true" ]
then
    ampy --port $DEVICE put src/
else
    ampy --port $DEVICE put src/main.py src/main.py
fi
echo Done!
