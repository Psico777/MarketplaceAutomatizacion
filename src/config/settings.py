"""
Configuration module for Facebook Marketplace Automation
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration class for the application"""

    # Facebook Credentials
    FACEBOOK_EMAIL = os.getenv('FACEBOOK_EMAIL', '')
    FACEBOOK_PASSWORD = os.getenv('FACEBOOK_PASSWORD', '')
    FACEBOOK_2FA_SECRET = os.getenv('FACEBOOK_2FA_SECRET', '')

    # Gemini AI Configuration
    # IMPORTANTE: nunca pongas la API key directo en el codigo. Ponla en tu .env
    # Consiguela en https://aistudio.google.com/apikey
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    AI_MODEL_IMAGE = os.getenv('AI_MODEL_IMAGE', 'gemini-2.5-flash')
    AI_MODEL_CHAT = os.getenv('AI_MODEL_CHAT', 'gemini-2.5-pro')

    # Browser Settings
    HEADLESS = os.getenv('HEADLESS', 'False').lower() == 'true'
    IMPLICIT_WAIT = int(os.getenv('IMPLICIT_WAIT', '10'))

    # Sesion persistente: perfil de Chrome guardado para NO re-loguear ni pedir 2FA
    # cada vez (mantiene cookies). Carpeta local, ignorada por git.
    USER_DATA_DIR = os.getenv('USER_DATA_DIR', os.path.abspath('browser_data/profile'))

    # --- Anti-baneo / comportamiento humano ---
    # Pausas aleatorias (segundos) entre acciones dentro de un formulario
    HUMAN_MIN_DELAY = float(os.getenv('HUMAN_MIN_DELAY', '0.4'))
    HUMAN_MAX_DELAY = float(os.getenv('HUMAN_MAX_DELAY', '1.2'))
    # Pausa (segundos) entre una publicacion y la siguiente
    LISTING_MIN_GAP = float(os.getenv('LISTING_MIN_GAP', '25'))
    LISTING_MAX_GAP = float(os.getenv('LISTING_MAX_GAP', '70'))
    # Limite de publicaciones por dia (protege la cuenta de Facebook)
    MAX_LISTINGS_PER_DAY = int(os.getenv('MAX_LISTINGS_PER_DAY', '20'))
    # Reintentos automaticos por producto fallido
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '2'))

    # Categoria por defecto del Marketplace (texto visible tal cual aparece en FB)
    DEFAULT_CATEGORY = os.getenv('DEFAULT_CATEGORY', 'Juguetes y juegos')
    DEFAULT_CONDITION = os.getenv('DEFAULT_CONDITION', 'Nuevo')

    # Image Settings
    MAX_IMAGE_SIZE = int(os.getenv('MAX_IMAGE_SIZE', '2048'))

    # URLs
    MARKETPLACE_URL = 'https://www.facebook.com/marketplace/create/item'
    MARKETPLACE_SELLING_URL = 'https://www.facebook.com/marketplace/you/selling'
    FACEBOOK_LOGIN_URL = 'https://www.facebook.com/'

    # Directories
    TEMP_DIR = 'temp_images'
    SCREENSHOTS_DIR = 'screenshots'
    LOGS_DIR = 'logs'
    HISTORY_FILE = os.getenv('HISTORY_FILE', 'listings_history.json')

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.FACEBOOK_EMAIL or not cls.FACEBOOK_PASSWORD:
            raise ValueError("Faltan credenciales de Facebook. Define FACEBOOK_EMAIL y FACEBOOK_PASSWORD en el .env")

        if not cls.GEMINI_API_KEY:
            raise ValueError("Falta la API key de Gemini. Define GEMINI_API_KEY en el .env (https://aistudio.google.com/apikey)")

        return True
