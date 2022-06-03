import json
import sys
import threading
import cv2
import speech_recognition as sr
from PyQt5 import QtGui
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QTableWidgetItem, QGraphicsColorizeEffect
from playsound import playsound

from microphone_handler import listen, speak

ERR_AUTHOR_NOT_FOUND = "Nu s-a putut găsi autorul introdus."


def err_author_doesnt_have(what):
    return f"Nu s-au putut găsi {what} pentru autorul introdus."


class Ui(QtWidgets.QMainWindow):
    selected_query: str
    speech_enabled: bool
    eye_control_enabled: bool
    voice_control_enabled: bool

    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi("qt-ui/ioc.ui", self)
        self.configure_triggers()

        # self.autorTExt.mousePressEvent = self.play_search_sound()

        self.speech_enabled = True
        self.eye_control_enabled = False
        self.voice_control_enabled = False
        self.selected_query = "citate"
        self._run_flag = self.voice_control_enabled

        with open("data/data.json", "r") as f:
            self.app_data = json.loads(f.read())

        with open("themes/main_theme_white.json", "r") as f:
            self.colors = json.loads(f.read())

        self.palette = self.palette()
        self.set_theme_colors()

        self.face_cascade = cv2.CascadeClassifier("eyetrack/haarcascade_frontalface_default.xml")
        threading.Thread(target=self.eye_tracker).start()
        self.voice_thread = threading.Thread(target=self.voice_handler_orchestrator)
        self.voice_thread.start()
        self.setPalette(self.palette)

        self.tableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.header = self.tableWidget.horizontalHeader()
        self.color_effect = QGraphicsColorizeEffect()
        self.show()

    def configure_triggers(self):
        self.quotesRadio.clicked.connect(lambda: self.set_query("citate"))
        self.booksRadio.clicked.connect(lambda: self.set_query("cărți"))
        self.articleRadio.clicked.connect(lambda: self.set_query("articole"))
        self.isSpeechEnabled.clicked.connect(self.toggle_speech)
        self.isEyeControlEnabled.clicked.connect(self.toggle_eye_control)
        self.isVoiceControlEnabled.clicked.connect(self.toggle_voice_control)
        self.searchButton.clicked.connect(self.search)
        self.showAuthorsButton.clicked.connect(self.show_authors)
        self.themeComboBox.currentTextChanged.connect(self.on_combobox_changed)
        self.tableWidget.clicked.connect(self.get_cell_value)

    def get_cell_value(self, index):
        speak(index.data(), self.speech_enabled)

    def set_theme_colors(self):
        self.palette.setColor(QPalette.Window, QColor(self.colors["bkg_colour"]))
        self.searchButton.setStyleSheet(f"QPushButton"
                                        f"{{background-color: {self.colors['btn_colour']}; border-radius : 5%;"
                                        f"color: {self.colors['btn_text_colour']};"
                                        "}"
                                        "QPushButton::hover"
                                        "{"
                                        f"background-color : {self.colors['btn_hover_colour']};"
                                        "}")
        self.showAuthorsButton.setStyleSheet(f"QPushButton"
                                             f"{{background-color: {self.colors['btn_colour']}; border-radius : 5%;"
                                             f"color: {self.colors['btn_text_colour']};"
                                             "}"
                                             "QPushButton::hover"
                                             "{"
                                             f"background-color : {self.colors['btn_hover_colour']};"
                                             "}")
        self.palette.setColor(QPalette.PlaceholderText, QColor(self.colors["placeholder_colour"]))
        self.palette.setColor(QPalette.WindowText, QColor(self.colors["general_text_colour"]))
        self.tableWidget.setStyleSheet(f"background-color: {self.colors['table_colour']}")
        self.setPalette(self.palette)

    def on_combobox_changed(self, value):
        filename = ""

        if value == "albă":
            filename = "themes/main_theme_white.json"
        elif value == "neagră":
            filename = "themes/main_theme_black.json"
        elif value == "albastră":
            filename = "themes/main_theme_dark_blue.json"

        with open(filename, "r") as f:
            self.colors = json.loads(f.read())

        self.set_theme_colors()

    def show_authors(self):
        self.refit_table(["Nume"])
        autori = self.app_data.keys()
        print(autori)
        self.tableWidget.setRowCount(len(autori))
        for idx, quote in enumerate(autori):
            self.tableWidget.setItem(idx, 0, QTableWidgetItem(quote))

    def set_table_to_quotes(self):
        if self.autorText.toPlainText() not in self.app_data:
            self.display_err(ERR_AUTHOR_NOT_FOUND)
            speak(f"Autorul {self.autorText.toPlainText()} nu există în baza noastră de date.",
                  self.speech_enabled)
        elif "citate" not in self.app_data[self.autorText.toPlainText()]:
            self.display_err(err_author_doesnt_have("citate"))
            speak(f"Nu au fost găsite {self.selected_query} de la {self.autorText.toPlainText()}",
                  self.speech_enabled)
        else:
            self.notificationLabel.setText("")
            self.refit_table(["Citat"])
            quote_data = self.app_data[self.autorText.toPlainText()]["citate"]
            self.tableWidget.setRowCount(len(quote_data))
            for idx, quote in enumerate(quote_data):
                self.tableWidget.setItem(idx, 0, QTableWidgetItem(quote))

            speak(f"Au fost găsite {len(quote_data)} {self.selected_query} de la {self.autorText.toPlainText()}",
                  self.speech_enabled)

    def display_err(self, err):
        self.notificationLabel.setText(err)
        self.color_effect.setColor(Qt.red)
        self.notificationLabel.setGraphicsEffect(self.color_effect)

    def set_table_to_books(self):
        if self.autorText.toPlainText() not in self.app_data:
            self.display_err(ERR_AUTHOR_NOT_FOUND)
            speak(f"Autorul {self.autorText.toPlainText()} nu există în baza noastră de date.",
                  self.speech_enabled)
        elif "cărți" not in self.app_data[self.autorText.toPlainText()]:
            self.display_err(err_author_doesnt_have("cărți"))
            speak(f"Nu au fost găsite {self.selected_query} de la {self.autorText.toPlainText()}",
                  self.speech_enabled)
        else:
            self.notificationLabel.setText("")
            self.refit_table(["Titlu", "Gen", "Anul publicării"])
            book_data = self.app_data[self.autorText.toPlainText()]["cărți"]
            self.tableWidget.setRowCount(len(book_data))
            for idx, book in enumerate(book_data):
                self.tableWidget.setItem(idx, 0, QTableWidgetItem(book["titlu"]))
                self.tableWidget.setItem(idx, 1, QTableWidgetItem(book["gen"]))
                self.tableWidget.setItem(idx, 2, QTableWidgetItem(str(book["anul_publicării"])))

            speak(f"Au fost găsite {len(book_data)} {self.selected_query} de la {self.autorText.toPlainText()}",
                  self.speech_enabled)

    def set_table_to_articles(self):
        if self.autorText.toPlainText() not in self.app_data:
            self.display_err(ERR_AUTHOR_NOT_FOUND)
            speak(f"Autorul {self.autorText.toPlainText()} nu există în baza noastră de date.",
                  self.speech_enabled)
        elif "articole" not in self.app_data[self.autorText.toPlainText()]:
            self.display_err(err_author_doesnt_have("articole"))
            speak(f"Nu au fost găsite {self.selected_query} de la {self.autorText.toPlainText()}",
                  self.speech_enabled)
        else:
            self.notificationLabel.setText("")
            self.refit_table(["Titlu", "Anul publicării"])
            article_data = self.app_data[self.autorText.toPlainText()]["articole"]
            self.tableWidget.setRowCount(len(article_data))
            for idx, article in enumerate(article_data):
                self.tableWidget.setItem(idx, 0, QTableWidgetItem(article["titlu"]))
                self.tableWidget.setItem(idx, 1, QTableWidgetItem(str(article["anul_publicării"])))

            speak(f"Au fost găsite {len(article_data)} {self.selected_query} de la {self.autorText.toPlainText()}",
                  self.speech_enabled)

    def refit_table(self, columns):
        self.tableWidget.setColumnCount(len(columns))
        self.tableWidget.setHorizontalHeaderLabels(columns)
        self.tableWidget.resizeColumnsToContents()
        for i in range(len(columns)):
            self.header.setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)

    def set_query(self, query_type):
        self.selected_query = query_type
        self.playsound_w_check("sounds/radio_check.mp3")

    def toggle_speech(self):
        self.speech_enabled = not self.speech_enabled
        self.play_toggle(self.speech_enabled)

    def toggle_eye_control(self):
        self.eye_control_enabled = not self.eye_control_enabled
        self.play_toggle(self.eye_control_enabled)

    def toggle_voice_control(self):
        if self.voice_control_enabled:
            self._run_flag = False
        else:
            self._run_flag = True

        self.voice_control_enabled = not self.voice_control_enabled
        self.play_toggle(self.voice_control_enabled)

    def play_toggle(self, on):
        if on:
            self.playsound_w_check("sounds/toggle_on.mp3")
        else:
            self.playsound_w_check("sounds/toggle_off.mp3")

    def search(self):
        print(self.selected_query)
        if self.selected_query == "citate":
            self.set_table_to_quotes()
        elif self.selected_query == "cărți":
            self.set_table_to_books()
        elif self.selected_query == "articole":
            self.set_table_to_articles()

    def playsound_w_check(self, sound: str):
        if self.speech_enabled:
            playsound(sound)

    def voice_handler_orchestrator(self):
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()

        while True:
            if self._run_flag:
                text = listen(recognizer, microphone)
                if not text["success"] and text["error"] == "API unavailable":
                    print("ERROR: {}\nclose program".format(text["error"]))
                    break
                while not text["success"]:
                    if not self._run_flag:
                        continue
                    speak("Nu am înțeles.", self.speech_enabled)
                    text = listen(recognizer, microphone)

                recognized_text = text["transcription"].lower()

                recognized_text_words = recognized_text.split(" ")

                if "selectează" in recognized_text_words and "citate" in recognized_text_words:
                    self.set_query("citate")
                    self.quotesRadio.toggle()

                if "selectează" in recognized_text_words and "cărți" in recognized_text_words:
                    self.set_query("cărți")
                    self.booksRadio.toggle()

                if "selectează" in recognized_text_words and "articole" in recognized_text_words:
                    self.set_query("articole")
                    self.articleRadio.toggle()

                if "pornește" in recognized_text_words and "controlul" in recognized_text_words and "ochii" in recognized_text_words:
                    if not self.eye_control_enabled:
                        self.toggle_eye_control()
                        self.isEyeControlEnabled.toggle()
                    else:
                        speak("Este deja pornit.", self.speech_enabled)

                if "pornește" in recognized_text_words and "controlul" in recognized_text_words and "vocea" in recognized_text_words:
                    if not self.voice_control_enabled:
                        self.toggle_voice_control()
                        self.isVoiceControlEnabled.toggle()
                    else:
                        speak("Este deja pornit.", self.speech_enabled)

                if "pornește" in recognized_text_words and "feedback" in recognized_text_words and "audio" in recognized_text_words:
                    if not self.speech_enabled:
                        self.toggle_speech()
                        self.isSpeechEnabled.toggle()
                    else:
                        speak("Este deja pornit.", self.speech_enabled)

                if "oprește" in recognized_text_words and "controlul" in recognized_text_words and "ochii" in recognized_text_words:
                    if self.eye_control_enabled:
                        self.toggle_eye_control()
                        self.isEyeControlEnabled.toggle()
                    else:
                        speak("Este deja oprit.", self.speech_enabled)

                if "oprește" in recognized_text_words and "controlul" in recognized_text_words and "vocea" in recognized_text_words:
                    if self.voice_control_enabled:
                        self.toggle_voice_control()
                        self.isVoiceControlEnabled.toggle()
                    else:
                        speak("Este deja oprit.", self.speech_enabled)

                if "oprește" in recognized_text_words and "feedback" in recognized_text_words and "audio" in recognized_text_words:
                    if self.speech_enabled:
                        self.toggle_speech()
                        self.isSpeechEnabled.toggle()
                    else:
                        speak("Este deja oprit.", self.speech_enabled)

                if "completează" in recognized_text_words:
                    index = recognized_text_words.index("completează")
                    try:
                        words = recognized_text_words[index + 1:]
                        for idx, word in enumerate(words):
                            words[idx] = word[0].upper() + word[1:]
                        self.autorText.setPlainText(" ".join(words))
                        print(words)
                    except Exception as e:
                        print(e)
                        speak("Te rog repetă.", self.speech_enabled)

                print(text["transcription"].lower())

    def eye_tracker(self):
        # construire stream video
        videoStream = cv2.VideoCapture(-1)
        eye_cascade = cv2.CascadeClassifier("eyetrack/haarcascade_eye_tree_eyeglasses.xml")
        while True:
            if self.eye_control_enabled:
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
                        # ecuație de transformare fereastra poarta

                        print(f"x={x} \n y={y} \n w={w} \n h={h}")
                        roi_gray = gray[y:y + h, x:x + w]
                        roi_color = cvImg[y:y + h, x:x + w]
                        eyes = eye_cascade.detectMultiScale(roi_gray)
                        for (ex, ey, ew, eh) in eyes:
                            cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 3)

                        # cv2.imshow("cv", cvImg)
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
