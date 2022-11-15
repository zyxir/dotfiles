#!/bin/sh

# Get the path of this script.
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

# Install basic dot files.
cp -v $SCRIPTPATH/dot-bashrc ~/.bashrc
cp -v $SCRIPTPATH/dot-bash_profile ~/.bash_profile
cp -v $SCRIPTPATH/dot-gitconfig ~/.gitconfig

# Install fontconfig configuration.
mkdir -vp $HOME/.config/fontconfig/
cp -v $SCRIPTPATH/fonts.conf $HOME/.config/fontconfig/

# Install Fcitx 5 themes and configs.
mkdir -vp $HOME/.local/share/fcitx5/themes/
cp -v $SCRIPTPATH/fcitx/themes/* $HOME/.local/share/fcitx5/themes/ -r
mkdir -vp $HOME/.config/fcitx5/conf/
cp -v $SCRIPTPATH/fcitx/config $HOME/.config/fcitx5/
cp -v $SCRIPTPATH/fcitx/profile $HOME/.config/fcitx5/
cp -v $SCRIPTPATH/fcitx/conf/* $HOME/.config/fcitx5/conf/
