import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-123'
    
    # Supported languages (expanded list)
    LANGUAGES = {
        'en': 'English',
        'hi': 'Hindi',
        'fr': 'French',
        'es': 'Spanish',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'zh': 'Chinese',
        'ja': 'Japanese',
        'ar': 'Arabic',
        'bn': 'Bengali',
        'pa': 'Punjabi',
        'ta': 'Tamil',
        'te': 'Telugu',
        'mr': 'Marathi',
        'ur': 'Urdu',
        'nl': 'Dutch',
        'ko': 'Korean'
    }

    # Special handling for certain language pairs
    MODEL_MAPPING = {
        # Asian languages to English
        ('hi', 'en'): 'Helsinki-NLP/opus-mt-hi-en',
        ('bn', 'en'): 'Helsinki-NLP/opus-mt-bn-en',
        ('zh', 'en'): 'Helsinki-NLP/opus-mt-zh-en',
        ('ja', 'en'): 'Helsinki-NLP/opus-mt-ja-en',
        ('ko', 'en'): 'Helsinki-NLP/opus-mt-ko-en',
        ('ta', 'en'): 'Helsinki-NLP/opus-mt-ta-en',
        
        # European languages to English
        ('fr', 'en'): 'Helsinki-NLP/opus-mt-fr-en',
        ('es', 'en'): 'Helsinki-NLP/opus-mt-es-en',
        ('de', 'en'): 'Helsinki-NLP/opus-mt-de-en',
        ('it', 'en'): 'Helsinki-NLP/opus-mt-it-en',
        ('ru', 'en'): 'Helsinki-NLP/opus-mt-ru-en',
        
        # English to other languages
        ('en', 'hi'): 'Helsinki-NLP/opus-mt-en-hi',
        ('en', 'fr'): 'Helsinki-NLP/opus-mt-en-fr',
        ('en', 'es'): 'Helsinki-NLP/opus-mt-en-es',
        ('en', 'de'): 'Helsinki-NLP/opus-mt-en-de',
        ('en', 'zh'): 'Helsinki-NLP/opus-mt-en-zh',
        ('en', 'ta'): 'facebook/nllb-200-distilled-600M',  # Better Tamil support
        
        # Between non-English languages
        ('fr', 'es'): 'Helsinki-NLP/opus-mt-fr-es',
        ('es', 'fr'): 'Helsinki-NLP/opus-mt-es-fr',
        ('de', 'fr'): 'Helsinki-NLP/opus-mt-de-fr'
    }

    # Fallback models
    MULTI_TO_EN = 'Helsinki-NLP/opus-mt-mul-en'  # Many languages to English
    EN_TO_MULTI = 'Helsinki-NLP/opus-mt-en-mul'  # English to many languages
    MULTILINGUAL = 'facebook/nllb-200-distilled-600M'  # Better multilingual support
    
    # Audio settings
    MAX_AUDIO_DURATION = 30  # seconds
    ALLOWED_AUDIO_EXTENSIONS = {'wav', 'mp3', 'ogg', 'flac'}

    # Model download settings
    MODEL_CACHE_DIR = os.path.join(os.getcwd(), "model_cache")
    HF_CACHE_DIR = os.path.join(os.getcwd(), "hf_cache")
    
    @classmethod
    def create_dirs(cls):
        """Create required directories"""
        os.makedirs(cls.MODEL_CACHE_DIR, exist_ok=True)
        os.makedirs(cls.HF_CACHE_DIR, exist_ok=True)

# Initialize directories
Config.create_dirs()