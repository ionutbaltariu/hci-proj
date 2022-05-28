import sys
import json
import cv2
import threading
import speech_recognition as sr
from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QTableWidgetItem
from playsound import playsound
from PyQt5 import QtGui
from microphone_handler import VoiceHandler


class Ui(QtWidgets.QMainWindow):
    selected_query: str
    speech_enabled: bool
    eye_control_enabled: bool
    voice_control_enabled: bool

    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('ioc.ui', self)
        self.quotesRadio.clicked.connect(lambda: self.set_query('citate'))
        self.booksRadio.clicked.connect(lambda: self.set_query('cărți'))
        self.articleRadio.clicked.connect(lambda: self.set_query('articole'))
        self.isSpeechEnabled.clicked.connect(self.toggle_speech)
        self.isEyeControlEnabled.clicked.connect(self.toggle_eye_control)
        self.isVoiceControlEnabled.clicked.connect(self.toggle_voice_control)
        self.searchButton.clicked.connect(self.search)
        # self.autorTExt.mousePressEvent = self.play_search_sound()

        self.speech_enabled = False
        self.eye_control_enabled = False
        self.voice_control_enabled = False
        self.selected_query = "citate"
        self._run_flag = self.voice_control_enabled

        with open("colours.json", "r") as f:
            self.colors = json.loads(f.read())

        self.palette = self.palette()
        self.palette.setColor(QPalette.Window, QColor(self.colors["bkg_colour"]))
        self.palette.setColor(QPalette.Button, QColor(self.colors["btn_colour"]))
        self.palette.setColor(QPalette.ButtonText, QColor(self.colors["btn_text_colour"]))
        self.palette.setColor(QPalette.PlaceholderText, QColor(self.colors["placeholder_colour"]))
        self.palette.setColor(QPalette.WindowText, QColor(self.colors["general_text_colour"]))

        self.voice_handler = VoiceHandler()
        self.face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
        # threading.Thread(target=self.eye_tracker).start()
        self.voice_thread = threading.Thread(target=self.voice_handler_orchestrator)
        self.voice_thread.start()
        self.setPalette(self.palette)

        self.tableWidget.setRowCount(1)
        self.tableWidget.setColumnCount(1)
        self.tableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.show()

    def set_table_to_quotes(self):
        self.tableWidget.setColumnCount(1)
        self.tableWidget.setHorizontalHeaderLabels(["Citat"])
        self.tableWidget.setItem(0, 0, QTableWidgetItem("Cogito ergo sum."))
        self.tableWidget.resizeColumnsToContents()
        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)

        with open("data.json", "r") as f:
            data = json.loads(f.read())
            quote_data = data[self.autorText.toPlainText()]["citate"]
            self.tableWidget.setRowCount(len(quote_data))
            print(quote_data)
            for idx, quote in enumerate(quote_data):
                self.tableWidget.setItem(idx, 0, QTableWidgetItem(quote))
            self.tableWidget.setItem(2, 0, QTableWidgetItem("ceva"))

    def set_table_to_books(self):
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setHorizontalHeaderLabels(["Titlu", "Gen", "Anul publicării"])
        self.tableWidget.resizeColumnsToContents()
        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)

        with open("data.json", "r") as f:
            data = json.loads(f.read())
            book_data = data[self.autorText.toPlainText()]["cărți"]
            self.tableWidget.setRowCount(len(book_data))
            print(book_data)
            for idx, book in enumerate(book_data):
                self.tableWidget.setItem(idx, 0, QTableWidgetItem(book["titlu"]))
                self.tableWidget.setItem(idx, 1, QTableWidgetItem(book["gen"]))
                self.tableWidget.setItem(idx, 2, QTableWidgetItem(str(book["anul_publicării"])))

    def set_table_to_articles(self):
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setHorizontalHeaderLabels(["Titlu", "Anul publicării"])
        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

        with open("data.json", "r") as f:
            data = json.loads(f.read())
            article_data = data[self.autorText.toPlainText()]["articole"]
            self.tableWidget.setRowCount(len(article_data))
            for idx, article in enumerate(article_data):
                self.tableWidget.setItem(idx, 0, QTableWidgetItem(article["titlu"]))
                self.tableWidget.setItem(idx, 1, QTableWidgetItem(str(article["anul_publicării"])))

    def set_query(self, query_type):
        self.selected_query = query_type
        print(self.selected_query)
        self.playsound_w_check("sounds/radio_check.mp3")

    def toggle_speech(self):
        self.speech_enabled = not self.speech_enabled
        self.play_toggle(self.speech_enabled)

    def toggle_eye_control(self):
        self.eye_control_enabled = not self.eye_control_enabled
        self.play_toggle(self.eye_control_enabled)

    def toggle_voice_control(self):
        self.voice_control_enabled = not self.voice_control_enabled

        if self.voice_control_enabled:
            self._run_flag = True
        else:
            self._run_flag = False

        self.play_toggle(self.voice_control_enabled)

    def play_toggle(self, on):
        if on:
            self.playsound_w_check("sounds/toggle_on.mp3")
        else:
            self.playsound_w_check("sounds/toggle_off.mp3")

    def search(self):
        print(self.selected_query)
        if self.selected_query == "citate":
            # search for quotes, display in app
            self.set_table_to_quotes()
        elif self.selected_query == "cărți":
            # search for books, display in app
            self.set_table_to_books()
        elif self.selected_query == "articole":
            # search for articles, display in app
            self.set_table_to_articles()

        if self.speech_enabled:
            self.voice_handler.speak(f"Se caută {self.selected_query} de la {self.autorText.toPlainText()}",
                                     self.speech_enabled)

    def playsound_w_check(self, sound: str):
        if self.speech_enabled:
            playsound(sound)

    def voice_handler_orchestrator(self):
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()

        while True:
            if self._run_flag:
                text = self.voice_handler.listen(recognizer, microphone)
                if not text["success"] and text["error"] == "API unavailable":
                    print("ERROR: {}\nclose program".format(text["error"]))
                    break
                while not text["success"]:
                    if self._run_flag == False:
                        continue
                    self.voice_handler.speak("Nu am înțeles.", self.speech_enabled)
                    text = self.voice_handler.listen(recognizer, microphone)

                recognized_text = text["transcription"].lower()

                recognized_text_words = recognized_text.split(' ')

                if 'selectează' in recognized_text_words and 'citate' in recognized_text_words:
                    self.set_query('citate')
                    self.quotesRadio.toggle()

                if 'selectează' in recognized_text_words and 'cărți' in recognized_text_words:
                    self.set_query('cărți')
                    self.booksRadio.toggle()

                if 'selectează' in recognized_text_words and 'articole' in recognized_text_words:
                    self.set_query('articole')
                    self.articleRadio.toggle()

                if 'pornește' in recognized_text_words and 'controlul' in recognized_text_words and 'ochii' in recognized_text_words:
                    if not self.eye_control_enabled:
                        self.toggle_eye_control()
                        self.isEyeControlEnabled.toggle()
                    else:
                        self.voice_handler.speak("Este deja pornit.", self.speech_enabled)

                if 'pornește' in recognized_text_words and 'controlul' in recognized_text_words and 'vocea' in recognized_text_words:
                    if not self.voice_control_enabled:
                        self.toggle_voice_control()
                        self.isVoiceControlEnabled.toggle()
                    else:
                        self.voice_handler.speak("Este deja pornit.", self.speech_enabled)

                if 'pornește' in recognized_text_words and 'feedback' in recognized_text_words and 'audio' in recognized_text_words:
                    if not self.speech_enabled:
                        self.toggle_speech()
                        self.isSpeechEnabled.toggle()
                    else:
                        self.voice_handler.speak("Este deja pornit.", self.speech_enabled)

                if 'oprește' in recognized_text_words and 'controlul' in recognized_text_words and 'ochii' in recognized_text_words:
                    if self.eye_control_enabled:
                        self.toggle_eye_control()
                        self.isEyeControlEnabled.toggle()
                    else:
                        self.voice_handler.speak("Este deja oprit.", self.speech_enabled)

                if 'oprește' in recognized_text_words and 'controlul' in recognized_text_words and 'vocea' in recognized_text_words:
                    if self.voice_control_enabled:
                        self.toggle_voice_control()
                        self.isVoiceControlEnabled.toggle()
                    else:
                        self.voice_handler.speak("Este deja oprit.", self.speech_enabled)

                if 'oprește' in recognized_text_words and 'feedback' in recognized_text_words and 'audio' in recognized_text_words:
                    if self.speech_enabled:
                        self.toggle_speech()
                        self.isSpeechEnabled.toggle()
                    else:
                        self.voice_handler.speak("Este deja oprit.", self.speech_enabled)

                if 'scrie' in recognized_text_words:
                    index = recognized_text_words.index('scrie')
                    try:
                        words = recognized_text_words[index + 1:]
                        self.autorText.setPlainText(' '.join(words))
                    except Exception as e:
                        print(e)
                        self.voice_handler.speak("Te rog repetă.", self.speech_enabled)

                    print(words)

                print(text["transcription"].lower())

    def eye_tracker(self):
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
                faceRects = self.face_cascade.detectMultiScale(gray, 1.3, 5)
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
                    if len(eyes) > 0:
                        xt = x - eyes[0][0]
                        yt = y - eyes[0][1]
                    else:
                        xt = 0
                        yt = 0
                    # ....
                    # snap to grid
                    # avand in vedere ca mouse-ul nu va sta fix pe ecran, se va adauga un filtru
                    # suplimentar ce va consta intr-un grid avand cate un punct in centrul
                    # elementului activ de pe interfața (buton, meniu etc) orice coordonate (xt,yt)
                    # aflate in aria unui element activ vor fi modificate astfel incat sa preia
                    # coordonatele centrului elementului respectiv
                    if len(eyes) > 0:
                        xg = x - eyes[0][0]
                        yg = y - eyes[0][1]
                    else:
                        xg = 0
                        yg = 0
                    # ....

                    QtGui.QCursor.setPos(xg, yg)
                    # daca cursorul este ținut in aria respectivă un timp de 2 secunde generați un
                    # eveniment click stanga
                    # ....
                    # if time > 2sec:
                    #     pyautogui.leftClick()
                    # actualizare imagine pe interfața
                    # self.change_pixmap_signal.emit(cv_img)
                    if cv2.waitKey(5) == 27:
                        break


app = QtWidgets.QApplication(sys.argv)
window = Ui()
app.exec_()
