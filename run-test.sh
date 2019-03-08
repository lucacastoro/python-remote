#!/bin/bash

TEMPLOG=/tmp/jsuidbfuia.log

function at_exit {
  rm -f $TEMPLOG
}

trap "rm -f $TEMPLOG" EXIT

ROOT=$(dirname $(realpath $0))

# build or update the image
docker build -t ssh-server $ROOT &>$TEMPLOG || {
  echo 'Image build failed:'
  cat $TEMPLOG
  exit 1
}

# run the container (detached)
docker run --rm -d -h test -p 2222:22 ssh-server &>$TEMPLOG || {
  echo 'Could not start the container:'
  cat $TEMPLOG
  exit 1
}

# execute the tests and store the result
$ROOT/test.py; RESULT=$?

# stop (and remove) the container
for container in $(docker ps | grep ssh-server | cut -d' ' -f1); do
  docker stop $container &>$TEMPLOG || {
    echo "Error while stopping container $container:"
    cat $TEMPLOG
  }
done

#return the test result
exit $RESULT
