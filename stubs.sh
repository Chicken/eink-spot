#!/usr/bin/env bash

rm -rf .vscode/stub-types
python3 -m pip install micropython-esp32-stubs==1.22.0.post1 --target "$PWD/.vscode/stub-types" --no-user
