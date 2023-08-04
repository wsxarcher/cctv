# importing libraries
import cv2
import numpy
from time import sleep, monotonic
import os
from os import getpid, getppid
from threading import current_thread
import itertools
from multiprocessing.managers import SyncManager
from queue import PriorityQueue
# import manager dict multiprocessing
# from multiprocessing.managers import BaseManager

manager = SyncManager()
manager.register('PriorityQueue', PriorityQueue)
manager.start()

shared_frames_all = []

enabled_cams = [4]

number_of_cams = len(enabled_cams)

for i in range(number_of_cams):
    shared_frames_all.append(manager.dict())

stop_worker = manager.list([False]*number_of_cams)
IS_GUI = bool(os.environ.get('DISPLAY'))

print("Cam loaded")

def streamer(video_index, watcher_id):
    print(f"Stream {video_index} started")
    try:
        q = manager.PriorityQueue()
        shared_frames_all[video_index][watcher_id] = q
        while True:
            print(f"streaming cam {video_index} to {watcher_id}")

            if stop_worker[video_index]:
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

# Defining a function motionDetection
def motionDetection(video_index):
    frame_counter = 0
    print(f"Motion {video_index} started")
    # capturing video in real time
    cap = cv2.VideoCapture(enabled_cams[video_index])
    win_name = "output"
    #cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    cap.set(cv2.CAP_PROP_FPS, 10)

    wait_until_focus = monotonic() + 2
    while monotonic() < wait_until_focus:
        cap.read()

    # reading frames sequentially
    ret, frame1 = cap.read()
    ret, frame2 = cap.read()

    while cap.isOpened():

        # difference between the frames
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
                flag, encoded_img = cv2.imencode('.jpg', frame1)
                q.put((-frame_counter, encoded_img))
            except Exception as e:
                print(e)

        if isGUI():
            cv2.imshow(win_name, frame1)
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