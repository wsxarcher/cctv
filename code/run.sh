set -ex

export VIDEO_DEVICE="/dev/video4"
export HOST_PORT=8001
export DEBUG=1

docker buildx build -t marcobartoli/fp .
docker run -it \
    -e "DEBUG=$DEBUG" \
    -v "$PWD/project:/app/project" \
    -v "$PWD/static:/app/static" \
    -v "$PWD/templates:/app/templates" \
    -v "$PWD/data:/app/data" \
    --device "$VIDEO_DEVICE:$VIDEO_DEVICE" -p $HOST_PORT:8000 marcobartoli/fp $@