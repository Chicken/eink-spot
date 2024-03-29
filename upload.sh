#!/usr/bin/env bash

DEVICE=/dev/ttyUSB0

if [ "$APP_ONLY" != "true" ] && [ "$ONLY_APP" != "true" ]
then
    echo Removing old code...
    rshell --port $DEVICE --quiet rm -r /pyboard/src
fi
echo Adding new code...
if [ "$APP_ONLY" != "true" ] && [ "$ONLY_APP" != "true" ]
then
    ampy --port $DEVICE put src/
else
    ampy --port $DEVICE put src/app.py src/app.py
fi
echo Done!
