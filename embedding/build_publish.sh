#!/bin/bash

# Set these variables
DOCKER_USERNAME="tjmlabs"
IMAGE_NAME="paliembed"
# version is today's date
VERSION=$(date +'%Y%m%d') # example: 20210101
cd ./embedding
# Build the Docker image
docker build --platform linux/amd64 --tag $DOCKER_USERNAME/$IMAGE_NAME:$VERSION .

# Push the image to Docker Hub
docker push $DOCKER_USERNAME/$IMAGE_NAME:$VERSION