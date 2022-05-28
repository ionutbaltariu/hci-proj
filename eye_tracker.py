import cv2


def eye_tracker():
    # construire stream video
    videoStream = cv2.VideoCapture(-1)
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier('haarcascade_eye_tree_eyeglasses.xml')
    while True:
        # preluare imagine
        ret, cvImg = videoStream.read()
        if ret:
            # flip horizontal imagine
            cvImg = cv2.flip(cvImg, 1)
            # conversie gray scale
            gray = cv2.cvtColor(cvImg, cv2.COLOR_BGR2GRAY)
            # detecție caracteristici
            faceRects = face_cascade.detectMultiScale(gray, 1.3, 5)
            # intr-o imagine pot fi mai multe fețe (caracteristici cautate)
            for (x, y, w, h) in faceRects:
                # desenare unui punct in centrul dreptunghiului ce incadreaza caracteristicile
                # detectate (fata/ochii)
                # coordonatele punctului sunt: x + int(w / 2), y + int(h / 2)
                cv2.rectangle(cvImg, (x, y, x + int(w / 2), y + int(h / 2)), (0, 255, 0), 3)

                # ecuație de transformare fereastra poarta

                print(f"x={x} \n y={y} \n w={w} \n h={h}")
                roi_gray = gray[y:y + h, x:x + w]
                roi_color = cvImg[y:y + h, x:x + w]
                eyes = eye_cascade.detectMultiScale(roi_gray)
                for (ex, ey, ew, eh) in eyes:
                    cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 3)

                # cv2.imshow('cv', cvImg)

                xt = x - eyes[0][0]
                yt = y - eyes[0][1]
                # ....
                # snap to grid
                # avand in vedere ca mouse-ul nu va sta fix pe ecran, se va adauga un filtru
                # suplimentar ce va consta intr-un grid avand cate un punct in centrul
                # elementului activ de pe interfața (buton, meniu etc) orice coordonate (xt,yt)
                # aflate in aria unui element activ vor fi modificate astfel incat sa preia
                # coordonatele centrului elementului respectiv
                xg = 0
                yg = 0
                # ....

                # QtGui.QCursor.setPos(xg, yg)
                # daca cursorul este ținut in aria respectivă un timp de 2 secunde generați un
                # eveniment click stanga
                # ....
                # if time > 2sec:
                #     pyautogui.leftClick()
                # actualizare imagine pe interfața
                # self.change_pixmap_signal.emit(cv_img)
                if cv2.waitKey(5) == 27:
                    break


eye_tracker()
