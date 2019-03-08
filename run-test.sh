#!/bin/bash

ROOT=$(dirname $(realpath $0))

[ -f $ROOT/test.py ] || {
  echo 'hmmmm... invalid directory'
  exit 1
}

[ $(stat -c %a $ROOT/ssh-key) != '600' ] && chmod 600 $ROOT/ssh-key

TEMPLOG=/tmp/jsuidbfuia.log

function at_exit {
  echo 'cleaning up the mess'
  rm -f $TEMPLOG
}

trap at_exit EXIT

echo 'building (or updating) the image'
docker build -t ssh-server $ROOT &>$TEMPLOG || {
  echo 'Image build failed:'
  cat $TEMPLOG
  exit 1
}

echo 'starting the container'
docker run --rm -d -h test -p 2222:22 ssh-server &>$TEMPLOG || {
  echo 'Could not start the container:'
  cat $TEMPLOG
  exit 1
}

echo 'executing the tests'
$ROOT/test.py; RESULT=$?

echo 'stopping (and removing) the container'
for container in $(docker ps | grep ssh-server | cut -d' ' -f1); do
  docker stop $container &>$TEMPLOG || {
    echo "Error while stopping container $container:"
    cat $TEMPLOG
  }
done

exit $RESULT
