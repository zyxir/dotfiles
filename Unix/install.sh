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

# Install Fcitx 5 themes and configurations.
mkdir -vp $HOME/.local/share/fcitx5/themes/
mkdir -vp $HOME/.config/fcitx5/conf/
cp -v $SCRIPTPATH/fcitx5/config $HOME/.config/fcitx5/
cp -v $SCRIPTPATH/fcitx5/profile $HOME/.config/fcitx5/
cp -v $SCRIPTPATH/fcitx5/conf/* $HOME/.config/fcitx5/conf/

# Install Xremap configuration.
mkdir -vp $HOME/.config/
cp -vr $SCRIPTPATH/xremap $HOME/.config/

# Load GNOME dconf files.
echo 'Configureing dconf...'
dconf load /org/gnome/desktop/wm/ < $SCRIPTPATH/gnome-dconf/wm.dconf
dconf load /org/gnome/mutter/ < $SCRIPTPATH/gnome-dconf/mutter.dconf
dconf load /org/gnome/settings-daemon/plugins/media-keys/ < $SCRIPTPATH/gnome-dconf/media-keys.dconf
echo 'Configureing dconf...done'