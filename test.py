from flask import Flask, request, jsonify
import speech_recognition as sr
from deep_translator import GoogleTranslator
import base64
import io
import traceback
from flask_cors import CORS
import wave
import tempfile
import os
from pydub import AudioSegment

app = Flask(__name__)
CORS(app)  # Enable CORS for browser requests

def convert_audio_to_wav(audio_bytes):
    """Convert audio bytes to WAV format using pydub"""
    try:
        # Try to load the audio with pydub (supports many formats)
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
        
        # Convert to WAV format (16-bit, mono, 16kHz for speech recognition)
        wav_audio = audio_segment.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        
        # Export to WAV bytes
        wav_io = io.BytesIO()
        wav_audio.export(wav_io, format="wav")
        wav_io.seek(0)
        return wav_io.getvalue()
    except Exception as e:
        print(f"Audio conversion failed: {e}")
        return None

@app.route('/translate-voice', methods=['POST'])
def translate_voice():
    try:
        print("Request received!")
        print(f"Content-Type: {request.content_type}")
        print(f"Request method: {request.method}")
        print(f"Form keys: {list(request.form.keys())}")
        print(f"Files keys: {list(request.files.keys())}")
        
        # Handle different request formats
        data = {}
        
        # Check if it's multipart/form-data (which includes binary audio)
        if request.content_type and 'multipart/form-data' in request.content_type:
            print("Processing multipart form data")
            data['src_lang'] = request.form.get('src_lang')
            data['dest_lang'] = request.form.get('dest_lang')
            
            # Handle audio data - could be in form or files
            if 'audio_data' in request.files:
                # Audio sent as file
                audio_file = request.files['audio_data']
                audio_bytes = audio_file.read()
                data['audio_data'] = audio_bytes  # Keep as bytes for now
                print(f"Audio from file: {len(audio_bytes)} bytes")
            elif 'audio_data' in request.form:
                # Audio sent as form field (might be base64 already)
                audio_data_form = request.form.get('audio_data')
                if isinstance(audio_data_form, str):
                    # Try to decode base64
                    try:
                        if ',' in audio_data_form:
                            audio_data_form = audio_data_form.split(',')[1]
                        data['audio_data'] = base64.b64decode(audio_data_form)
                    except:
                        data['audio_data'] = audio_data_form.encode()
                else:
                    data['audio_data'] = audio_data_form
                print("Audio from form field")
            else:
                return jsonify({'error': 'audio_data not found in request'}), 400
                
        elif request.content_type and 'application/json' in request.content_type:
            print("Processing JSON data")
            json_data = request.get_json()
            data['src_lang'] = json_data.get('src_lang')
            data['dest_lang'] = json_data.get('dest_lang')
            audio_data_json = json_data.get('audio_data')
            
            if isinstance(audio_data_json, str):
                # Decode base64
                try:
                    if ',' in audio_data_json:
                        audio_data_json = audio_data_json.split(',')[1]
                    data['audio_data'] = base64.b64decode(audio_data_json)
                except:
                    return jsonify({'error': 'Invalid base64 audio data'}), 400
            else:
                data['audio_data'] = audio_data_json
            
        else:
            print("Trying to parse as form data")
            if request.form:
                data = {
                    'src_lang': request.form.get('src_lang'),
                    'dest_lang': request.form.get('dest_lang'),
                    'audio_data': request.form.get('audio_data')
                }
                if isinstance(data['audio_data'], str):
                    try:
                        if ',' in data['audio_data']:
                            data['audio_data'] = data['audio_data'].split(',')[1]
                        data['audio_data'] = base64.b64decode(data['audio_data'])
                    except:
                        data['audio_data'] = data['audio_data'].encode()
            else:
                return jsonify({'error': 'Unable to parse request data'}), 400
            
        if not data:
            return jsonify({'error': 'No data received'}), 400
            
        print("Parsed data keys:", list(data.keys()) if data else "None")
        
        # Check if required fields are present
        if not data.get('src_lang'):
            return jsonify({'error': 'src_lang is required'}), 400
        if not data.get('dest_lang'):
            return jsonify({'error': 'dest_lang is required'}), 400
        if not data.get('audio_data'):
            return jsonify({'error': 'audio_data is required'}), 400
            
        src_lang = data['src_lang']
        dest_lang = data['dest_lang']
        audio_bytes = data['audio_data']
        
        print(f"Source language: {src_lang}")
        print(f"Destination language: {dest_lang}")
        print(f"Audio data type: {type(audio_bytes)}")
        print(f"Audio data length: {len(audio_bytes)} bytes")

        # Convert audio to WAV format first
        print("Converting audio to WAV format...")
        wav_bytes = convert_audio_to_wav(audio_bytes)
        
        if wav_bytes is None:
            return jsonify({'error': 'Unable to convert audio format. Please try recording again.'}), 400
            
        print(f"Converted audio length: {len(wav_bytes)} bytes")

        # Process audio with speech recognition
        recognizer = sr.Recognizer()
        
        try:
            # Use the converted WAV audio
            audio_io = io.BytesIO(wav_bytes)
            
            with sr.AudioFile(audio_io) as source:
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.2)
                audio = recognizer.record(source)
                
                # Use appropriate language code for speech recognition - expanded support for Indian languages
                lang_code = src_lang if src_lang in ['en', 'es', 'fr', 'de', 'it', 'pt', 'hi', 'kn', 'te', 'ta', 'ml', 'gu', 'bn', 'mr', 'pa'] else 'en'
                
                # For Google Speech Recognition, some languages need specific formatting
                if src_lang == 'kn':
                    lang_code = 'kn-IN'  # Kannada (India)
                elif src_lang == 'te':
                    lang_code = 'te-IN'  # Telugu (India)
                elif src_lang == 'hi':
                    lang_code = 'hi-IN'  # Hindi (India)
                elif src_lang == 'ta':
                    lang_code = 'ta-IN'  # Tamil (India)
                elif src_lang == 'ml':
                    lang_code = 'ml-IN'  # Malayalam (India)
                elif src_lang == 'gu':
                    lang_code = 'gu-IN'  # Gujarati (India)
                elif src_lang == 'bn':
                    lang_code = 'bn-IN'  # Bengali (India)
                elif src_lang == 'mr':
                    lang_code = 'mr-IN'  # Marathi (India)
                elif src_lang == 'pa':
                    lang_code = 'pa-IN'  # Punjabi (India)
                
                print(f"Using speech recognition language code: {lang_code}")
                text = recognizer.recognize_google(audio, language=lang_code)
                print(f"Recognized ({src_lang}): {text}")
                
        except sr.UnknownValueError:
            return jsonify({'error': 'Could not understand the audio. Please speak clearly and try again.'}), 400
        except sr.RequestError as e:
            return jsonify({'error': f'Speech recognition service error: {str(e)}'}), 500
        except Exception as e:
            print(f"Speech recognition failed: {e}")
            return jsonify({'error': f'Speech recognition failed: {str(e)}'}), 500

        # Translate text using deep-translator
        try:
            translator = GoogleTranslator(source=src_lang, target=dest_lang)
            translated_text = translator.translate(text)
            print(f"Translated ({src_lang}→{dest_lang}): {translated_text}")
        except Exception as e:
            return jsonify({'error': f'Translation error: {str(e)}'}), 500

        return jsonify({
            'success': True,
            'original_text': text,
            'translated_text': translated_text,
            'src_lang': src_lang,
            'dest_lang': dest_lang
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/translate-text', methods=['POST'])
def translate_text():
    """Simple text translation endpoint for testing"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400
            
        text = data.get('text', '')
        src_lang = data.get('src_lang', 'en')
        dest_lang = data.get('dest_lang', 'es')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        translator = GoogleTranslator(source=src_lang, target=dest_lang)
        translated_text = translator.translate(text)
        
        return jsonify({
            'success': True,
            'original_text': text,
            'translated_text': translated_text,
            'src_lang': src_lang,
            'dest_lang': dest_lang
        })
        
    except Exception as e:
        return jsonify({'error': f'Translation error: {str(e)}'}), 500

@app.route('/')
def home():
    return "Voice Translator Backend Running - Updated for Microphone Input"

@app.route('/test', methods=['GET', 'POST'])
def test():
    return jsonify({'message': 'Test endpoint working', 'method': request.method})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
