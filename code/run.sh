set -ex

export VIDEO_DEVICE="/dev/video4"
export HOST_PORT=8001

docker buildx build -t marcobartoli/fp .
docker run -v "$PWD/project:/final/project" --device "$VIDEO_DEVICE:$VIDEO_DEVICE" -p $HOST_PORT:8000 marcobartoli/fp $@