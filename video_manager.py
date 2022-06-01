import cv2
import pyautogui


class VideoManager:
    def __init__(self, int_width, int_height, cam_width, cam_height):
        self.cam_width = cam_width
        self.cam_height = cam_height

        self.interface_width = int_width
        self.interface_height = int_height

        self.face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

        self.close = False

    def calibrate(self, vid, direction):
        self.close = False
        calibrated_value = None

        for i in range(60):
            ret, frame = vid.read()
            frame = cv2.resize(frame, (self.cam_width, self.cam_height))
            if ret:
                cvImg = cv2.flip(frame, 1)
                gray = cv2.cvtColor(cvImg, cv2.COLOR_BGR2GRAY)
                faceRects = self.face_cascade.detectMultiScale(gray, 1.3, 5)

                for (x, y, w, h) in faceRects:
                    cvImg = cv2.rectangle(cvImg, (x, y), (x + w, y + h), (255, 0, 0), 3)
                    if direction == 'Left':
                        calibrated_value = x + w / 2
                    elif direction == 'Right':
                        calibrated_value = x + w / 2
                    elif direction == 'Up':
                        calibrated_value = y + h / 2
                    elif direction == 'Down':
                        calibrated_value = y + h / 2

            cv2.imshow('frame', cvImg)
            if cv2.waitKey(1) & 0xFF == ord('\r'):
                break

        print(calibrated_value)
        return calibrated_value

    def video_stream(self):
        vid = cv2.VideoCapture(0)

        xf_min = self.calibrate(vid, 'Left')
        xf_max = self.calibrate(vid, 'Right')
        yf_min = self.calibrate(vid, 'Up')
        yf_max = self.calibrate(vid, 'Down')

        while not self.close:
            ret, frame = vid.read()
            frame = cv2.resize(frame, (self.cam_width, self.cam_height))
            if ret:
                cvImg = cv2.flip(frame, 1)
                gray = cv2.cvtColor(cvImg, cv2.COLOR_BGR2GRAY)
                faceRects = self.face_cascade.detectMultiScale(gray, 1.3, 5)

                for (x, y, w, h) in faceRects:
                    cvImg = cv2.rectangle(cvImg, (x, y), (x + w, y + h), (255, 0, 0), 3)

                    xf = x + w / 2
                    yf = y + h / 2

                    if xf < xf_min:
                        xf = xf_min

                    if xf > xf_max:
                        xf = xf_max

                    if yf < yf_min:
                        yf = yf_min

                    if yf > yf_max:
                        yf = yf_max

                    xp_min = 0
                    xp_max = self.interface_width
                    yp_min = 0
                    yp_max = self.interface_height

                    xp = xf * ((xp_max - xp_min) / (xf_max - xf_min)) + xp_min - (
                            (xp_max - xp_min) / (xf_max - xf_min)) * xf_min
                    yp = yf * ((yp_max - yp_min) / (yf_max - yf_min)) + yp_min - (
                            (yp_max - yp_min) / (yf_max - yf_min)) * yf_min

                    xp = int(xp)
                    yp = int(yp)
                    xp = xp - xp % 50
                    yp = yp - yp % 50

                    if xp > self.interface_width:
                        xp = self.interface_width

                    if yp > self.interface_height:
                        yp = self.interface_height

                    cv2.imshow('frame', cvImg)
                    pyautogui.moveTo(xp / xp_max * 1920, yp / yp_max * 1080)

            if cv2.waitKey(1) & 0xFF == ord('r'):
                break

        vid.release()


v = VideoManager(800, 800, 400, 400)
v.video_stream()
