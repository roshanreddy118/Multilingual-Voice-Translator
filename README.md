🖥️ Frontend (React)

Features:

🎙️ Record and Stop audio using browser microphone.

🌐 Select source and destination languages (English + major Indian languages).

⚡ Send recorded audio to backend for processing.

🧾 Display both original and translated text.

🎧 Playback translated audio (if available).

💅 UI built with TailwindCSS – responsive and minimal.

Core Technologies:

React (Hooks)

TailwindCSS

MediaRecorder API

Fetch API for backend integration




🔧 Backend (Flask)

Features:

Converts audio to standard WAV (16kHz, mono).

Recognizes speech in 10+ languages using speech_recognition.

Translates text with deep_translator.

CORS-enabled for web integration.

Supports both /translate-voice and /translate-text endpoints.

Core Technologies:

Flask

speech_recognition

pydub

deep_translator

flask_cors

Python 3.10+




🧠 Future Enhancements

Add text-to-speech output for translated text

Support offline mode using local AI models (Whisper / MarianMT)

Enable live streaming translation for meetings or video calls

Deploy using Docker or AWS Lambda + S3
