from transformers import MarianMTModel, MarianTokenizer, AutoModelForSeq2SeqLM, AutoTokenizer
from config import Config
import sentencepiece
import torch
import logging
import os
from typing import Tuple, Dict, Union

# Configure environment and logging
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TRANSFORMERS_CACHE"] = Config.MODEL_CACHE_DIR
os.environ["HF_CACHE"] = Config.HF_CACHE_DIR
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Translator:
    def __init__(self):
        self.models: Dict[str, Tuple[Union[MarianMTModel, AutoModelForSeq2SeqLM], 
                                  Union[MarianTokenizer, AutoTokenizer]]] = {}
        self.config = Config()
        self._setup_cache()
        self._verify_language_pairs()
        self.preload_priority_models()

    def _setup_cache(self):
        """Create cache directories if they don't exist"""
        os.makedirs(self.config.MODEL_CACHE_DIR, exist_ok=True)
        os.makedirs(self.config.HF_CACHE_DIR, exist_ok=True)
        logger.info(f"Model cache directory: {self.config.MODEL_CACHE_DIR}")

    def _verify_language_pairs(self):
        """Verify all configured language pairs are supported"""
        for (src, tgt), model_name in self.config.MODEL_MAPPING.items():
            if src not in self.config.LANGUAGES or tgt not in self.config.LANGUAGES:
                logger.warning(f"Configured pair {src}-{tgt} uses unsupported language")

    def preload_priority_models(self):
        """Preload all bidirectional models from MODEL_MAPPING"""
        loaded = set()
        for (src, tgt), model_name in self.config.MODEL_MAPPING.items():
            if f"{src}-{tgt}" not in loaded:
                try:
                    self.get_model(src, tgt)
                    loaded.add(f"{src}-{tgt}")
                    if (tgt, src) in self.config.MODEL_MAPPING:
                        self.get_model(tgt, src)
                        loaded.add(f"{tgt}-{src}")
                except Exception as e:
                    logger.error(f"Preload failed for {src}-{tgt}: {str(e)}")

    def get_model(self, src_lang: str, tgt_lang: str) -> Tuple[Union[MarianMTModel, AutoModelForSeq2SeqLM], 
                                                             Union[MarianTokenizer, AutoTokenizer]]:
        """Get or load appropriate translation model with smart fallback"""
        model_key = f"{src_lang}-{tgt_lang}"
        
        if model_key not in self.models:
            try:
                model_name = self._determine_model(src_lang, tgt_lang)
                logger.info(f"Loading model: {model_name}")
                
                if "facebook/nllb" in model_name:
                    # Use Auto classes for NLLB models
                    model = AutoModelForSeq2SeqLM.from_pretrained(
                        model_name,
                        cache_dir=self.config.MODEL_CACHE_DIR
                    )
                    tokenizer = AutoTokenizer.from_pretrained(
                        model_name,
                        cache_dir=self.config.MODEL_CACHE_DIR
                    )
                else:
                    # Use Marian classes for OPUS models
                    model = MarianMTModel.from_pretrained(
                        model_name,
                        cache_dir=self.config.MODEL_CACHE_DIR
                    )
                    tokenizer = MarianTokenizer.from_pretrained(
                        model_name,
                        cache_dir=self.config.MODEL_CACHE_DIR
                    )
                
                # Ensure model is on correct device
                device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                model = model.to(device)
                
                self.models[model_key] = (model, tokenizer)
                
            except Exception as e:
                logger.error(f"Model load failed for {model_key}: {str(e)}")
                raise
                
        return self.models[model_key]

    def _determine_model(self, src_lang: str, tgt_lang: str) -> str:
        """Determine the best model for the language pair"""
        if (src_lang, tgt_lang) in self.config.MODEL_MAPPING:
            return self.config.MODEL_MAPPING[(src_lang, tgt_lang)]
        elif (tgt_lang, src_lang) in self.config.MODEL_MAPPING:
            return self.config.MODEL_MAPPING[(tgt_lang, src_lang)]
        elif tgt_lang == 'en':
            return self.config.MULTI_TO_EN
        elif src_lang == 'en':
            return self.config.EN_TO_MULTI
        else:
            return self.config.MULTILINGUAL

    def translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
        """Handle translation with device awareness and language-specific optimizations"""
        if not text.strip():
            return ""
            
        if src_lang == tgt_lang:
            return text
            
        try:
            model, tokenizer = self.get_model(src_lang, tgt_lang)
            device = model.device
            
            # Handle NLLB model's language codes
            if "facebook/nllb" in str(type(model)):
                src_lang_code = self._get_nllb_lang_code(src_lang)
                text = f"{src_lang_code} {text}"  # NLLB requires prefix
                
            # Tokenize and move inputs to model's device
            inputs = tokenizer(
                [text],
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=512
            ).to(device)  # Critical - move inputs to model's device
            
            # Generate translation
            with torch.no_grad():
                if torch.cuda.is_available():
                    with torch.cuda.amp.autocast():
                        outputs = model.generate(
                            **inputs,
                            num_beams=4,
                            early_stopping=True
                        )
                else:
                    outputs = model.generate(
                        **inputs,
                        num_beams=4,
                        early_stopping=True
                    )
            
            # Decode and clean
            translated = tokenizer.batch_decode(
                outputs,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )[0]
            
            return self._post_process(translated, src_lang, tgt_lang)
            
        except Exception as e:
            logger.error(f"Translation failed: {str(e)}")
            return f"[Error: {str(e)}]"

    def _get_nllb_lang_code(self, lang: str) -> str:
        """Convert standard lang codes to NLLB specific codes"""
        nllb_codes = {
            'en': 'eng_Latn',
            'hi': 'hin_Deva',
            'ta': 'tam_Taml',
            'te': 'tel_Telu',
            'bn': 'ben_Beng',
            'mr': 'mar_Deva',
            'pa': 'pan_Guru',
            'ur': 'urd_Arab',
            'gu': 'guj_Gujr',
            'kn': 'kan_Knda',
            'ml': 'mal_Mlym',
            'or': 'ory_Orya',
            'as': 'asm_Beng',
            'ne': 'npi_Deva'
        }
        return nllb_codes.get(lang, f"{lang}_Latn")  # Default fallback

    def _post_process(self, text: str, src_lang: str, tgt_lang: str) -> str:
        """Enhanced post-processing with language-specific rules"""
        # Common fixes
        text = text.replace(" ,", ",").replace(" .", ".")
        
        # Language-specific cleaning
        if tgt_lang == 'ta':
            text = text.replace('"', '').replace("'", "")
        elif tgt_lang == 'hi':
            text = text.replace(" ' ", "'")
        elif tgt_lang == 'ar':
            text = text[::-1].strip()  # RTL handling
            
        # Remove NLLB artifacts if present
        if text.startswith(('▁', ' ')):
            text = text.lstrip('▁ ')
            
        return text.strip()

# Initialize translator with persistent caching
translator = Translator()