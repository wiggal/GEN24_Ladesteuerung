#!/bin/bash
cd `dirname $0`
if (( $# == 0))
then
    echo " Bitte Pythonscript als Parameter angeben!"
    exit
elif [[ ! -f "$1" ]]
then
    echo " Pythonscript \"$1\" existiert nicht!"
    exit
elif [[ "`file $1`" != *"Python script"* ]]
then
    echo "\"$1\" ist kein Pythonscript!"
    exit
fi

/usr/bin/python3 $1 $2 >>Crontab.log 2>&1
