"""
Test script to verify installation and configuration
Run this before using the main automation system
"""
import sys
import os

print("=" * 60)
print("Facebook Marketplace Automation - System Check")
print("=" * 60)
print()

# Test 1: Python version
print("[1/8] Checking Python version...")
if sys.version_info >= (3, 8):
    print(f"     ✓ Python {sys.version.split()[0]} (OK)")
else:
    print(f"     ✗ Python {sys.version.split()[0]} (Need 3.8+)")
    sys.exit(1)

# Test 2: Required packages
print("\n[2/8] Checking required packages...")
required_packages = {
    'selenium': 'Selenium WebDriver',
    'PIL': 'Pillow (Image processing)',
    'PyPDF2': 'PDF processing',
    'pdf2image': 'PDF to image conversion',
    'genai': 'Google Gemini AI',
    'dotenv': 'Environment variables',
    'pyotp': '2FA support'
}

all_packages_ok = True
for package, description in required_packages.items():
    try:
        if package == 'PIL':
            import PIL
        elif package == 'genai':
            from google import genai
        elif package == 'dotenv':
            import dotenv
        else:
            __import__(package)
        print(f"     ✓ {description}")
    except ImportError:
        print(f"     ✗ {description} (NOT INSTALLED)")
        all_packages_ok = False

if not all_packages_ok:
    print("\n     Run: pip install -r requirements.txt")
    sys.exit(1)

# Test 3: Check .env file
print("\n[3/8] Checking .env file...")
if os.path.exists('.env'):
    print("     ✓ .env file exists")
else:
    print("     ✗ .env file not found")
    print("     Create .env file from .env.example")
    sys.exit(1)

# Test 4: Load configuration
print("\n[4/8] Loading configuration...")
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    from config.settings import Config
    print("     ✓ Configuration loaded")
except Exception as e:
    print(f"     ✗ Error loading configuration: {e}")
    sys.exit(1)

# Test 5: Check credentials
print("\n[5/8] Checking credentials...")
credentials_ok = True

if Config.FACEBOOK_EMAIL and '@' in Config.FACEBOOK_EMAIL:
    print(f"     ✓ Facebook email configured")
else:
    print(f"     ✗ Facebook email not configured")
    credentials_ok = False

if Config.FACEBOOK_PASSWORD:
    print(f"     ✓ Facebook password configured")
else:
    print(f"     ✗ Facebook password not configured")
    credentials_ok = False

if Config.GEMINI_API_KEY and len(Config.GEMINI_API_KEY) > 20:
    print(f"     ✓ Gemini API key configured")
    if Config.GEMINI_API_KEY == 'AIzaSyDiyBs75bDIsM7kTl36DT0mccOVFFfETiI':
        print(f"     ⚠ Using demo API key - get your own at https://makersuite.google.com/app/apikey")
else:
    print(f"     ✗ Gemini API key not configured or invalid")
    credentials_ok = False

if Config.FACEBOOK_2FA_SECRET:
    print(f"     ✓ 2FA secret configured (optional)")
else:
    print(f"     ⚠ 2FA secret not configured (optional)")

if not credentials_ok:
    print("\n     Please configure credentials in .env file")
    sys.exit(1)

# Test 6: Check Chrome/Chromium
print("\n[6/8] Checking Chrome browser...")
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    
    print("     ✓ Chrome WebDriver available")
except Exception as e:
    print(f"     ✗ Chrome WebDriver not available: {e}")
    print("     Install Chrome: https://www.google.com/chrome/")

# Test 7: Test Gemini AI connection
print("\n[7/8] Testing Gemini AI connection...")
try:
    from google import genai
    client = genai.Client(api_key=Config.GEMINI_API_KEY)
    
    # Try a simple request
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents='Hello, respond with OK if you receive this.'
    )
    
    if response.text:
        print("     ✓ Gemini AI connection successful")
    else:
        print("     ✗ Gemini AI returned empty response")
except Exception as e:
    print(f"     ✗ Gemini AI connection failed: {e}")
    print("     Check your API key at: https://makersuite.google.com/app/apikey")

# Test 8: Check directories
print("\n[8/8] Checking directories...")
directories = [Config.TEMP_DIR, Config.SCREENSHOTS_DIR]
for directory in directories:
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            print(f"     ✓ Created {directory}/")
        except Exception as e:
            print(f"     ✗ Could not create {directory}/: {e}")
    else:
        print(f"     ✓ {directory}/ exists")

# Summary
print("\n" + "=" * 60)
print("System Check Complete!")
print("=" * 60)
print()
print("✓ All checks passed! You can now run the main script:")
print("  python main.py create --pdf your_product.pdf")
print()
print("For more help, see:")
print("  - README.md for general usage")
print("  - USAGE_GUIDE.md for detailed guide")
print("  - examples.py for code examples")
print()
