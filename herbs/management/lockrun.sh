#!/bin/bash

locker="/tmp/herb-locked"

homed="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $homed && flock -w 10 $locker $homed/run.sh


sleep 5m
rm $locker