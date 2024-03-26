#!/usr/bin/env bash

rm -rf .vscode/Pico-W-Stub
python3 -m pip install micropython-esp32-stubs==1.22.0.post1 --target "$PWD/.vscode/Pico-W-Stub" --no-user
