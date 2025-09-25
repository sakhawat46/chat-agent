import os
import requests
from django.conf import settings

API_KEY = settings.OPENAI_API_KEY
BASE = "https://api.openai.com/v1"
JSON_HEADERS = {"Authorization": f"Bearer {API_KEY}"}

STT_MODEL_PRIMARY = "gpt-4o-mini-transcribe"
STT_MODEL_FALLBACK = "whisper-1"
CHAT_MODEL = "gpt-4o-mini"
TTS_MODEL = "tts-1"

def transcribe_audio(file_path: str, language: str = "en") -> str:
    """
    Try gpt-4o-mini-transcribe; fallback to whisper-1.
    """
    url = f"{BASE}/audio/transcriptions"
    for model in (STT_MODEL_PRIMARY, STT_MODEL_FALLBACK):
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "application/octet-stream")}
            data = {"model": model, "language": language, "response_format": "json"}
            resp = requests.post(url, headers=JSON_HEADERS, files=files, data=data, timeout=120)
        if resp.ok:
            return resp.json().get("text", "")
    resp.raise_for_status()
    return ""

def chat_completion(messages: list[dict], model: str = CHAT_MODEL) -> str:
    url = f"{BASE}/chat/completions"
    payload = {"model": model, "messages": messages, "temperature": 0.3}
    resp = requests.post(url, headers={**JSON_HEADERS, "Content-Type": "application/json"}, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()

def synthesize_speech(text: str, voice: str = "alloy", fmt: str = "mp3") -> bytes:
    url = f"{BASE}/audio/speech"
    payload = {"model": TTS_MODEL, "voice": voice, "input": text, "format": fmt}
    resp = requests.post(url, headers={**JSON_HEADERS, "Content-Type": "application/json"}, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.content
