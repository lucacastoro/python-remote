#!/bin/bash

pytest='pytest==4.3.0'
image='ssh-server'
port=2222
host='test'
user='test'
root=$(dirname $(realpath $0))

[ -f $root/remote.py ] || {
  echo 'hmmmm... invalid directory'
  exit 1
}

[ "$PWD" != "$root" ] && cd $root

[ $(stat -c %a ./ssh-key) != '600' ] && {
  echo 'adjusting key permissions'
  chmod 600 ./ssh-key
}

templog=$(mktemp)

function remove_log {
  echo 'cleaning up the mess'
  rm -f $templog
}

trap remove_log EXIT

echo 'building (or updating) the image'
docker build -t $image . &>$templog || {
  echo 'Image build failed:'
  cat $templog
  exit 1
}

echo 'starting the container'
docker run --rm -d -h $host -p $port:22 $image &>$templog || {
  echo 'Could not start the container:'
  cat $templog
  exit 1
}

echo 'executing the tests'
pytest -vv $@; result=$?

echo 'stopping (and removing) the container'
for container in $(docker ps | grep $image | cut -d' ' -f1); do
  docker stop $container &>$templog || {
    echo "Error while stopping container $container:"
    cat $templog
  }
done

exit $result
