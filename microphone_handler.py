import os
import gtts
import speech_recognition as sr
from playsound import playsound


def speak(text, is_speech_enabled):
    try:
        if is_speech_enabled:
            tts = gtts.gTTS(text, lang="ro")
            tts.save("sunet.mp3")
            playsound("sunet.mp3")
            os.remove("sunet.mp3")
    except Exception:
        pass


def listen(recognizer: sr.Recognizer, microphone: sr.Microphone):
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    response = {
        "success": True,
        "error": None,
        "transcription": None
    }

    try:
        response["transcription"] = recognizer.recognize_google(audio, language="ro-RO")
    except sr.RequestError:
        response["success"] = False
        response["error"] = "API indisponibil."
    except sr.UnknownValueError:
        response["success"] = False
        response["error"] = "Nu am înțeles. Te rog să repeți."

    return response
