#!/bin/bash

WORK_DIR=$(pwd)
CLIPS_DIR=$WORK_DIR/clips_core_source_630
DOWNLOAD_URL="https://downloads.sourceforge.net/project/clipsrules/CLIPS/6.30/clips_core_source_630.zip"

wget -O clips.zip $DOWNLOAD_URL

unzip clips.zip

cd $CLIPS_DIR

cp makefiles/makefile.lib core/Makefile

cd $CLIPS_DIR/core/

sed -i 's/gcc -c/gcc -fPIC -c/g' Makefile

make

ld -G *.o -o libclips.so

cd $WORK_DIR

sudo pip install --upgrade pip
sudo pip install --upgrade setuptools
sudo pip install --upgrade pytest

python setup.py build_ext --include-dirs $CLIPS_DIR/core/ --library-dirs $CLIPS_DIR/core/
python setup.py install

CFLAGS="-I$CLIPS_DIR/core/" LDFLAGS="-L$CLIPS_DIR/core/" python clips/clips_build.py

mv _clips* clips/
