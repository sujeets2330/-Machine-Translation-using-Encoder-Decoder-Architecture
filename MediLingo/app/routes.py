from flask import Blueprint, request, jsonify, render_template
from app.core.translator import translator
from config import Config
import whisper
import os
from datetime import datetime

bp = Blueprint('main', __name__)
stt_model = whisper.load_model("base")

@bp.route('/')
def index():
    return render_template('index.html', config=Config())

@bp.route('/translate', methods=['POST'])
def translate_text():
    data = request.get_json()
    text = data.get('text', '')
    src_lang = data.get('src_lang', 'en')
    tgt_lang = data.get('tgt_lang', 'en')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
        
    try:
        translated = translator.translate(text, src_lang, tgt_lang)
        return jsonify({
            'original': text,
            'translated': translated,
            'src_lang': src_lang,
            'tgt_lang': tgt_lang
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
        
    audio_file = request.files['audio']
    src_lang = request.form.get('src_lang', 'en')
    
    try:
        # Save temporary audio file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_path = f"temp_audio_{timestamp}.wav"
        audio_file.save(audio_path)
        
        # Transcribe using Whisper
        result = stt_model.transcribe(audio_path, language=src_lang if src_lang != 'auto' else None)
        text = result['text']
        
        # Clean up
        os.remove(audio_path)
        
        return jsonify({
            'text': text,
            'language': src_lang
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500