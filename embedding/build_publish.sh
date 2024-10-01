#!/bin/bash

# Usage:
# ./build_publish.sh local  # For local build
# ./build_publish.sh cloud  # For cloud build

# Set these variables
DOCKER_USERNAME="tjmlabs"
IMAGE_NAME="paliembed"
VERSION=$(date +'%Y%m%d') # version is today's date, example: 20210101

# Determine version suffix and Dockerfile based on argument
case "$1" in
    local)
        VERSION_SUFFIX="local"
        DOCKERFILE="Dockerfile.local"
        ;;
    cloud)
        VERSION_SUFFIX="cloud"
        DOCKERFILE="Dockerfile"
        ;;
    *)
        echo "Usage: $0 {local|cloud}"
        exit 1
        ;;
esac

VERSION="${VERSION}-${VERSION_SUFFIX}"

cd ./embedding

# Build the Docker image
docker build --platform linux/amd64 -f $DOCKERFILE --tag $DOCKER_USERNAME/$IMAGE_NAME:$VERSION .

# Push the image to Docker Hub
docker push $DOCKER_USERNAME/$IMAGE_NAME:$VERSION