# importing libraries
import cv2
import numpy
from time import sleep
import os

stop_worker = False
IS_GUI = bool(os.environ.get('DISPLAY'))

print("Cam loaded")

def isGUI():
    return IS_GUI

# Defining a function motionDetection
def motionDetection():
    # capturing video in real time
    cap = cv2.VideoCapture(4)
    win_name = "output"
    #cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    cap.set(cv2.CAP_PROP_FPS, 10)

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
            cv2.putText(frame1, "STATUS: {}".format('MOTION DETECTED'), (10, 60), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (217, 10, 10), 2)
            print("Motion detection")

        #cv2.drawContours(frame1, contours, -1, (0, 255, 0), 2)

        if isGUI():
            cv2.imshow(win_name, frame1)
        frame1 = frame2
        ret, frame2 = cap.read()

        sleep_time = 60

        if stop_worker:
            print("Stopping worker")
            break

        if isGUI():
            if cv2.waitKey(sleep_time) == 27:
                break
        else:
            sleep(sleep_time/1000)

    cap.release()
    if isGUI():
        cv2.destroyAllWindows()

def main():
    motionDetection()

if __name__ == "__main__":
    main()