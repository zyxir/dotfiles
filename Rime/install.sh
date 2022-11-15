#!/bin/sh

# Get the path of this script.
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")
OLDDIR=$(pwd)

# Install all configurations.
SRC_LIST=$(find $SCRIPTPATH/cangjie5 \
                $SCRIPTPATH/cangjie6 \
                $SCRIPTPATH/double_pinyin \
                $SCRIPTPATH/luna_pinyin \
                -name "*.yaml")
SRC_LIST="${SRC_LIST} $SCRIPTPATH/default.custom.yaml"
DEST="$HOME/.local/share/fcitx5/rime/"
mkdir -pv $DEST

for f in $SRC_LIST
do
    cp -v $f $DEST
done
