set -ex

# Support most videos/streams via ffmpeg 

SOURCES=(url file)
SOURCES_CAM_INDEX=(100 101)

SOURCES_CAM_INDEX_JOINED=$(IFS=, ; echo "${SOURCES_CAM_INDEX[*]}")

echo $SOURCES_CAM_INDEX_JOINED

sudo modprobe -r v4l2loopback
sudo modprobe v4l2loopback devices=${#SOURCES[@]} exclusive_caps=1,1 video_nr="$SOURCES_CAM_INDEX_JOINED" 'card_label=virtcam,virtcam2'

for (( i=0; i<${#SOURCES[@]}; i++ ));
do
    SOURCE="${SOURCES[i]}"
    CAM_INDEX="${SOURCES_CAM_INDEX[i]}"
    VIDEO_DEV="/dev/video$CAM_INDEX"
    
    sudo chmod 777 "$VIDEO_DEV"
    if [[ -f "$SOURCE" ]]; then
        # Loop video for testing
        ffmpeg -stream_loop -1 -re -i "$SOURCE" -vcodec rawvideo -threads 0 -f v4l2 "$VIDEO_DEV" &
    else
        # MJPEG
        ffmpeg -use_wallclock_as_timestamps 1 -i "$SOURCE" -vf "format=yuv420p,setpts=PTS-STARTPTS" -vsync 0 -vcodec rawvideo -threads 0 -f v4l2 "$VIDEO_DEV" &
    fi
done

wait < <(jobs -p)