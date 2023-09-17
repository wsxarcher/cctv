import re
import cv2
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator
import numpy
from time import sleep, monotonic
import os
from os import getpid, getppid
from threading import current_thread
import itertools
from glob import glob
from multiprocessing.managers import SyncManager
from queue import PriorityQueue
# import manager dict multiprocessing
# from multiprocessing.managers import BaseManager
from . import db_logic

manager = SyncManager()
manager.register('PriorityQueue', PriorityQueue)
manager.start()

shared_frames_all = []


def get_dev_cameras():
    cams = []
    devs = os.listdir("/dev")
    match_name = "index"
    for dev in devs:
        matches = re.match(fr"video(?P<{match_name}>\d+)", dev)
        if matches:
            index = int(matches.groupdict()[match_name])
            cams.append(index)
    return sorted(cams)

enabled_cams = get_dev_cameras()

number_of_cams = len(enabled_cams)

for i in range(number_of_cams):
    shared_frames_all.append(manager.dict())

stop_worker = manager.list([False]*number_of_cams)
IS_GUI = bool(os.environ.get('DISPLAY'))
TMP_STREAMING = os.environ.get('TMP_STREAMING')
SEGMENTS_URL = "SEGMENTS_URL"

model = YOLO('/usr/src/ultralytics/yolov8n.pt')
print("Cam loaded")

def streamer(video_index, watcher_id, check_session):
    print(f"Stream {video_index} started")
    try:
        q = manager.PriorityQueue()
        shared_frames_all[video_index][watcher_id] = q
        while True:
            print(f"streaming cam {video_index} to {watcher_id}")

            if stop_worker[video_index] or check_session() is None:
                raise Exception("stop")

            _, frame = q.get()
            while not q.empty():
                try:
                    q.get(block=False)
                except:
                    continue
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                   bytearray(frame) + b'\r\n')
    except:
        del shared_frames_all[video_index][watcher_id]
        print("removed watcher {} from cam {}".format(watcher_id, i))

def isGUI():
    return IS_GUI

def delete_old_tmp():
    for playlist in glob(os.path.join(TMP_STREAMING, "*.m3u8")):
        try:
            print(f"Removing {playlist}")
            os.remove(playlist)
        except OSError:
            print("Error while deleting file old playlist")

    for fragment in glob(os.path.join(TMP_STREAMING, "*.ts")):
        try:
            print(f"Removing {fragment}")
            os.remove(fragment)
        except OSError:
            print("Error while deleting file old fragment")

# Defining a function motionDetection
def motionDetection(video_index):
    delete_old_tmp()
    seconds_check_settings = 1
    detection_enabled = db_logic.intrusiondetection(video_index)
    frame_counter = 0
    print(f"Motion {video_index} started")
    # capturing video in real time
    cap = cv2.VideoCapture(enabled_cams[video_index])
    win_name = "output"
    #cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    fps = 10
    cap.set(cv2.CAP_PROP_FPS, fps)
    get_fps = int(cap.get(cv2.CAP_PROP_FPS))
    print(get_fps)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) // 6
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) // 6

    wait_until_focus = monotonic() + 2
    while monotonic() < wait_until_focus:
        cap.read()

    # reading frames sequentially
    ret, frame1 = cap.read() 
    ret, frame2 = cap.read()

    print(width, height)

    gst_pipeline = f'appsrc is-live=true block=true ! videoconvert ! x264enc tune=zerolatency key-int-max=1 ! h264parse ! hlssink3 location={TMP_STREAMING}/segment-{video_index}-%05d.ts playlist-location={TMP_STREAMING}/{video_index}.m3u8 playlist-root={SEGMENTS_URL} max-files=5 target-duration=2 playlist-type=2'
    writer = cv2.VideoWriter(gst_pipeline,
                0, 10, (640, 480))
    if not writer.isOpened():
        print('video writer failed')

    while cap.isOpened():
        if frame_counter % fps*seconds_check_settings == 0:
            detection_enabled_old = detection_enabled
            detection_enabled = db_logic.intrusiondetection(video_index)
            if detection_enabled != detection_enabled_old:
                print("Intrusion detection", "enabled" if detection_enabled else "disabled")
        # difference between the frames
        if detection_enabled:
            diff = cv2.absdiff(frame1, frame2)
            diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(diff_gray, (5, 5), 0)
            _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
            dilated = cv2.dilate(thresh, None, iterations=3)
            contours, _ = cv2.findContours(
                dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                (x, y, w, h) = cv2.boundingRect(contour)
                if cv2.contourArea(contour) < 900:
                    continue
                cv2.rectangle(frame1, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame1, "INTRUSION DETECTED", (10, 60), cv2.FONT_HERSHEY_SIMPLEX,
                            1, (217, 10, 10), 2)
                print("INTRUSION detection!!")

            resized = cv2.resize(frame1,(640,480),fx=0,fy=0, interpolation = cv2.INTER_CUBIC)
            results = model(resized, verbose=False)
            #print(result)

            annotator = Annotator(resized)

            for r in results:
                for box in r.boxes:
                    b = box.xyxy[0]
                    c = box.cls
                    annotator.box_label(b, f"{r.names[int(c)]} {float(box.conf):.2}")
        else:
            resized = cv2.resize(frame1,(640,480),fx=0,fy=0, interpolation = cv2.INTER_CUBIC)


        writer.write(resized)

        #cv2.drawContours(frame1, contours, -1, (0, 255, 0), 2)

        if stop_worker[video_index]:
            print("Stopping worker")
            #for q in shared_frames_all[video_index]:
            #    q.task_done()
            #for q in shared_frames_all[video_index]:
            #    q.join()
            break

        frame_counter += 1

        for watcher_id, q in shared_frames_all[video_index].items():
            try:
                flag, encoded_img = cv2.imencode('.jpg', resized)
                q.put((-frame_counter, encoded_img))
            except Exception as e:
                print(e)

        if isGUI():
            cv2.imshow(win_name, resized)
        frame1 = frame2
        ret, frame2 = cap.read()

        sleep_time = 60


        if isGUI():
            if cv2.waitKey(sleep_time) == 27:
                break
        else:
            sleep(sleep_time/1000)

    cap.release()
    if isGUI():
        cv2.destroyAllWindows()
    print(f"Motion {video_index} stopped")

def shutdown(threads):
    global stop_worker
    print("Shutting down cam!!")
    for i in range(number_of_cams):
        stop_worker[i] = True
    for t in threads:
        t.join()
    manager.shutdown()
    manager.join()

def main():
    motionDetection(4)

if __name__ == "__main__":
    main()