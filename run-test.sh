#!/bin/bash

ROOT=$(dirname $(realpath $0))

# build or update the image
docker build -t ssh-server $ROOT &>/dev/null

# run the container (detached)
docker run --rm -d -h test -p 2222:22 ssh-server &>/dev/null

# execute the tests
$ROOT/test.py

# stop (and remove) the container
for container in $(docker ps | grep ssh-server | cut -d' ' -f1); do
  docker stop $container &>/dev/null
done
