#!/usr/bin/env bash

aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin 375479154925.dkr.ecr.eu-west-1.amazonaws.com
docker build -t eth2-keygen .
docker tag eth2-keygen:latest 375479154925.dkr.ecr.eu-west-1.amazonaws.com/eth2-keygen:latest
docker push 375479154925.dkr.ecr.eu-west-1.amazonaws.com/eth2-keygen:latest
