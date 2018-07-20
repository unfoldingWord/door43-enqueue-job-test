#!/usr/bin/env bash

# Parameter $1 is expected to be develop or master

if [ "$1" == "master" ]; then
    echo "Making MASTER image and pushing it" ;
    make imageMaster && make pushMasterImage
else
    echo "Making DEVELOP image and pushing it" ;
    make imageDev && make pushDevImage
fi
