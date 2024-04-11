#!/bin/bash

# This file build the installer package into a single file, put it at the root
# of the dotfiles directory, and remove all temporary files.

# Compile to a single file.
shiv -c installer -o ../../install.pyz .

# Remove temporary files.
rm -rf ./build ./*.egg-info/
