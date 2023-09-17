set -ex

export VIDEO_DEVICES=(/dev/video4) # give user permission
export HOST_PORT=8001
export DEBUG=1
export DRAW_BOXES=1
export TMP_STREAMING="/tmp/streaming/"

docker buildx build --build-arg USER_UID=$(id -u) --build-arg USER_GID=$(id -g) -t marcobartoli/fp .
docker rm fp_container || true
docker run -it \
    --name fp_container \
    -e "DEBUG=$DEBUG" \
    -v "$PWD/project:/app/project" \
    -v "$PWD/static:/app/static" \
    -v "$PWD/templates:/app/templates" \
    -v "$PWD/data:/app/data" \
    --mount "type=tmpfs,destination=$TMP_STREAMING" \
    -e "DRAW_BOXES=$DRAW_BOXES" \
    -e "TMP_STREAMING=$TMP_STREAMING" \
    -e "PUSHOVER_USER_KEY=$PUSHOVER_USER_KEY" \
    -e "PUSHOVER_APP_TOKEN=$PUSHOVER_APP_TOKEN" \
    ${VIDEO_DEVICES[@]/#/--device=} -p $HOST_PORT:8000 marcobartoli/fp $@