#!/bin/bash

flock -w 10 ./locked ./run.sh

