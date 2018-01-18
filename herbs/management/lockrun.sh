#!/bin/bash


homed="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $homed && flock -w 10 /tmp/herb-locked $homed/run.sh

