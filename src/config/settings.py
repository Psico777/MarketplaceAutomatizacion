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
    # ⚠️ WARNING: The default API key below is for DEMONSTRATION ONLY
    # It may be rate-limited, restricted, or revoked at any time
    # For production use, you MUST obtain your own API key from:
    # https://makersuite.google.com/app/apikey
    # and set it in your .env file as GEMINI_API_KEY=your_key_here
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyDiyBs75bDIsM7kTl36DT0mccOVFFfETiI')
    AI_MODEL_IMAGE = os.getenv('AI_MODEL_IMAGE', 'gemini-2.5-flash')
    AI_MODEL_CHAT = os.getenv('AI_MODEL_CHAT', 'gemini-2.5-pro')
    
    # Browser Settings
    HEADLESS = os.getenv('HEADLESS', 'False').lower() == 'true'
    IMPLICIT_WAIT = int(os.getenv('IMPLICIT_WAIT', '10'))

    # Perfil persistente de Chrome -> la sesion (login + 2FA) sobrevive entre
    # ejecuciones, imprescindible para el responder 24/7 en Pi / DigitalOcean.
    CHROME_PROFILE_DIR = os.getenv('CHROME_PROFILE_DIR', '')
    # Binario de Chrome (util en ARM / headless donde no esta en el PATH).
    CHROME_BINARY = os.getenv('CHROME_BINARY', '')
    # Factor de velocidad humana (>1 mas lento, p.ej. en un Pi modesto).
    HUMAN_SPEED = float(os.getenv('HUMAN_SPEED', '1.0'))

    # Image Settings
    MAX_IMAGE_SIZE = int(os.getenv('MAX_IMAGE_SIZE', '2048'))

    # --- Responder automatico de Messenger ---------------------------------
    # Intervalo ALEATORIO entre rondas de respuestas (minutos). NO responde cada
    # 10s: espera de 3 a 8 min para no saturar la maquina ni delatarse como bot.
    RESPONDER_MIN_MINUTES = float(os.getenv('RESPONDER_MIN_MINUTES', '3'))
    RESPONDER_MAX_MINUTES = float(os.getenv('RESPONDER_MAX_MINUTES', '8'))
    # Maximo de hilos no leidos a responder por ronda (evita rafagas).
    RESPONDER_MAX_THREADS_PER_ROUND = int(os.getenv('RESPONDER_MAX_THREADS_PER_ROUND', '3'))
    # Contexto del negocio que la IA usa para responder (productos, precios...).
    BUSINESS_CONTEXT = os.getenv(
        'BUSINESS_CONTEXT',
        'SOMOS LK: tienda peruana de juguetes y novedades por mayor y menor. '
        'Compras por mayor desde la media docena (6 unidades, pueden ser surtidas). '
        'Tambien precios por docena, ciento y cajon. Pagos por Yape/transferencia. '
        'Contacto y pedidos por WhatsApp 995665397.'
    )

    # --- Grupos de Facebook ------------------------------------------------
    # URLs de grupos donde publicar (separadas por coma en el .env).
    FACEBOOK_GROUPS = [
        g.strip() for g in os.getenv('FACEBOOK_GROUPS', '').split(',') if g.strip()
    ]
    # URLs de grupos a los que UNIRSE automaticamente (separadas por coma).
    FACEBOOK_GROUPS_TO_JOIN = [
        g.strip() for g in os.getenv('FACEBOOK_GROUPS_TO_JOIN', '').split(',') if g.strip()
    ]
    # Pausa ALEATORIA entre publicaciones a grupos (minutos), anti-spam.
    GROUP_POST_MIN_MINUTES = float(os.getenv('GROUP_POST_MIN_MINUTES', '4'))
    GROUP_POST_MAX_MINUTES = float(os.getenv('GROUP_POST_MAX_MINUTES', '12'))

    # URLs
    MARKETPLACE_URL = 'https://web.facebook.com/marketplace/create/item'
    MARKETPLACE_SELLING_URL = 'https://www.facebook.com/marketplace/you/selling'
    FACEBOOK_LOGIN_URL = 'https://www.facebook.com/'
    MESSENGER_URL = 'https://www.facebook.com/messages/t/'

    # Directories
    TEMP_DIR = 'temp_images'
    SCREENSHOTS_DIR = 'screenshots'

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.FACEBOOK_EMAIL or not cls.FACEBOOK_PASSWORD:
            raise ValueError("Facebook credentials are required. Please set FACEBOOK_EMAIL and FACEBOOK_PASSWORD in .env file")

        if not cls.GEMINI_API_KEY:
            raise ValueError("Gemini API key is required. Please set GEMINI_API_KEY in .env file")

        return True
