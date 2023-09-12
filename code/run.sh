set -ex

export VIDEO_DEVICE="/dev/video4"
export HOST_PORT=8001
export DEBUG=1
export TMP_STREAMING="/tmp/streaming/"

docker buildx build -t marcobartoli/fp .
docker rm fp_container || true
docker run -it \
    --name fp_container \
    -e "DEBUG=$DEBUG" \
    -v "$PWD/project:/app/project" \
    -v "$PWD/static:/app/static" \
    -v "$PWD/templates:/app/templates" \
    -v "$PWD/data:/app/data" \
    --mount "type=tmpfs,destination=$TMP_STREAMING" \
    -e "TMP_STREAMING=$TMP_STREAMING" \
    --device "$VIDEO_DEVICE:$VIDEO_DEVICE" -p $HOST_PORT:8000 marcobartoli/fp $@