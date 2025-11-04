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
    
    # Image Settings
    MAX_IMAGE_SIZE = int(os.getenv('MAX_IMAGE_SIZE', '2048'))
    
    # URLs
    MARKETPLACE_URL = 'https://web.facebook.com/marketplace/create/item'
    MARKETPLACE_SELLING_URL = 'https://www.facebook.com/marketplace/you/selling'
    FACEBOOK_LOGIN_URL = 'https://www.facebook.com/'
    
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
