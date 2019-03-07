#!/bin/bash

docker run --rm -it -p 2222:22 ssh-server $@
