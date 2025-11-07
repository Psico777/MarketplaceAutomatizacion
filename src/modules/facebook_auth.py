"""
Facebook Authentication Module
Handles Facebook login with 2FA support using Selenium
"""
import time
import pyotp
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


class FacebookAuthenticator:
    """Handle Facebook authentication with 2FA support"""
    
    def __init__(self, email, password, two_fa_secret=None, headless=False, implicit_wait=10, twofa_callback=None):
        """
        Initialize Facebook Authenticator
        
        Args:
            email (str): Facebook email
            password (str): Facebook password
            two_fa_secret (str, optional): TOTP secret for 2FA
            headless (bool): Run browser in headless mode
            implicit_wait (int): Implicit wait time in seconds
            twofa_callback (callable, optional): Callback function for 2FA confirmation
        """
        self.email = email
        self.password = password
        self.two_fa_secret = two_fa_secret
        self.headless = headless
        self.implicit_wait = implicit_wait
        self.twofa_callback = twofa_callback
        self.driver = None
    
    def setup_driver(self):
        """Setup Chrome WebDriver"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
        
        # Essential options for modern Facebook interface
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Modern user agent to force modern Facebook UI
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
        
        # Force modern UI - no mobile/old versions
        chrome_options.add_argument('--force-device-scale-factor=1.0')
        
        # Disable old/basic mode redirects
        prefs = {
            'profile.default_content_setting_values.notifications': 2,
            'profile.default_content_setting_values.media_stream_camera': 2,
            'profile.default_content_setting_values.media_stream_mic': 2,
            'profile.default_content_setting_values.geolocation': 2
        }
        chrome_options.add_experimental_option('prefs', prefs)
        
        # ⚠️⚠️⚠️ IMPORTANT LEGAL WARNING ⚠️⚠️⚠️
        # The settings below attempt to hide automation detection
        # Using automation tools with Facebook may VIOLATE their Terms of Service
        # https://www.facebook.com/terms.php
        # You use this software AT YOUR OWN RISK
        # The authors are NOT responsible for any consequences including:
        # - Account suspension or termination
        # - Legal action from Facebook
        # - Any other damages or losses
        # By using this software, you acknowledge and accept these risks
        
        # Disable automation detection
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Install ChromeDriver with proper driver path
        driver_path = ChromeDriverManager().install()
        # Ensure we get the actual chromedriver binary, not a text file
        if driver_path.endswith('THIRD_PARTY_NOTICES.chromedriver') or not driver_path.endswith('chromedriver'):
            import os
            driver_dir = os.path.dirname(driver_path)
            # Look for the actual chromedriver binary
            for file in os.listdir(driver_dir):
                if file == 'chromedriver' or file == 'chromedriver.exe':
                    driver_path = os.path.join(driver_dir, file)
                    break
        
        service = Service(driver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(self.implicit_wait)
        
        # Execute script to prevent detection
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return self.driver
    
    def login(self, url='https://www.facebook.com/'):
        """
        Login to Facebook
        
        Args:
            url (str): Facebook URL to navigate to
            
        Returns:
            webdriver: Chrome driver instance if successful, None otherwise
        """
        try:
            if not self.driver:
                self.setup_driver()
            
            print("Navigating to Facebook...")
            self.driver.get(url)
            time.sleep(0.2)  # Reducido de 3 a 0.2
            
            # Check if already logged in
            if self._is_logged_in():
                print("Already logged in!")
                return self.driver
            
            # Find and fill email
            print("Entering email...")
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            email_field.clear()
            email_field.send_keys(self.email)
            
            # Find and fill password
            print("Entering password...")
            password_field = self.driver.find_element(By.ID, "pass")
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Click login button
            print("Clicking login button...")
            login_button = self.driver.find_element(By.NAME, "login")
            login_button.click()
            
            time.sleep(0.2)  # Reducido de 5 a 0.2
            
            # Take screenshot for debugging
            import os
            os.makedirs('screenshots', exist_ok=True)
            self.driver.save_screenshot('screenshots/after_login.png')
            print("Screenshot saved to screenshots/after_login.png")
            
            # Check for 2FA
            if self._check_2fa_required():
                print("2FA required, handling...")
                if not self._handle_2fa():
                    print("Failed to handle 2FA")
                    return None
            
            # Check for other security checks
            self._handle_security_checks()
            
            # Verify login
            if self._is_logged_in():
                print("Login successful!")
                return self.driver
            else:
                print("Login failed - not logged in after process")
                print(f"Current URL: {self.driver.current_url}")
                print(f"Page title: {self.driver.title}")
                # Take another screenshot
                self.driver.save_screenshot('screenshots/login_failed.png')
                print("Screenshot saved to screenshots/login_failed.png")
                return None
                
        except Exception as e:
            print(f"Error during login: {e}")
            return None
    
    def _is_logged_in(self):
        """Check if user is logged in"""
        try:
            # Check for presence of user menu or specific logged-in elements
            self.driver.find_element(By.XPATH, "//div[@role='navigation']")
            return True
        except NoSuchElementException:
            return False
    
    def _check_2fa_required(self):
        """Check if 2FA is required"""
        try:
            # Check current URL for 2FA indicators
            if 'two_step_verification' in self.driver.current_url or 'checkpoint' in self.driver.current_url:
                return True
            # Look for 2FA code input field
            self.driver.find_element(By.ID, "approvals_code")
            return True
        except NoSuchElementException:
            return False
    
    def _handle_2fa(self):
        """
        Handle 2FA authentication
        
        Returns:
            bool: True if 2FA handled successfully, False otherwise
        """
        try:
            # Si no hay secret configurado O es inválido, usar aprobación manual
            if not self.two_fa_secret or len(self.two_fa_secret) < 16:
                print("\n" + "="*60)
                print("🔐 2FA REQUERIDO - Aprobación en tu Celular")
                print("="*60)
                print("Facebook está solicitando autenticación de dos factores.")
                print("\n📱 INSTRUCCIONES:")
                print("1. Revisa tu celular - debe aparecer notificación de Facebook")
                print("2. Abre la app de Facebook y APRUEBA el inicio de sesión")
                print("3. Espera a que Chrome cargue tu perfil de Facebook")
                print("4. Cuando veas tu feed/inicio de Facebook, presiona ENTER aquí")
                print("\n⏳ El script está PAUSADO esperando tu confirmación...")
                print("="*60 + "\n")
                
                # Si hay callback (GUI), usarlo; sino usar input()
                if self.twofa_callback:
                    # GUI mode - callback bloqueará hasta que usuario confirme
                    try:
                        result = self.twofa_callback()
                        if not result:
                            print("\n✗ Usuario canceló la confirmación 2FA")
                            return False
                    except Exception as e:
                        print(f"Error handling 2FA: {e}")
                        return False
                else:
                    # Terminal mode - usar input()
                    try:
                        input(">>> Presiona ENTER cuando estés dentro de Facebook: ")
                    except KeyboardInterrupt:
                        print("\n✗ Cancelado por el usuario")
                        return False
                    except:
                        # Si falla el input (por ejemplo en background), esperar un tiempo
                        print("No se pudo capturar input, esperando 60 segundos...")
                        time.sleep(60)
                
                print("\n✓ Continuando... verificando login...")
                time.sleep(1)  # Dar tiempo para que Facebook cargue después de aprobar
                
                # Verificar si el login fue exitoso
                if self._is_logged_in():
                    print("✓ 2FA completado exitosamente!")
                    return True
                else:
                    print("⚠ Verificando de nuevo...")
                    # Dar una segunda oportunidad
                    time.sleep(2)  # Dar más tiempo si no detectó el login inmediatamente
                    if self._is_logged_in():
                        print("✓ 2FA completado!")
                        return True
                    else:
                        print("✗ Login no completado. Por favor verifica:")
                        print("  - Que hayas aprobado en tu celular")
                        print("  - Que Chrome muestre tu feed de Facebook")
                        return False
            
            # Generate 2FA code automatically
            totp = pyotp.TOTP(self.two_fa_secret)
            code = totp.now()
            print(f"Generated 2FA code: {code}")
            
            # Enter 2FA code
            code_field = self.driver.find_element(By.ID, "approvals_code")
            code_field.clear()
            code_field.send_keys(code)
            
            # Click submit
            submit_button = self.driver.find_element(By.ID, "checkpointSubmitButton")
            submit_button.click()
            
            time.sleep(0.2)  # Reducido de 5 a 0.2
            
            # Handle "Don't save browser" option
            try:
                dont_save = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Not Now') or contains(text(), 'Don')]")
                dont_save.click()
                time.sleep(0.1)  # Reducido de 2 a 0.1
            except NoSuchElementException:
                pass
            
            return True
            
        except Exception as e:
            print(f"Error handling 2FA: {e}")
            return False
    
    def _handle_security_checks(self):
        """Handle various security checks that may appear"""
        try:
            # Check for "Save Login Info" popup
            try:
                not_now = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Not Now')]"))
                )
                not_now.click()
                time.sleep(0.1)  # Reducido de 2 a 0.1
            except TimeoutException:
                pass
            
            # Check for notification prompts
            try:
                not_now = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Not Now') or contains(text(), 'Block')]")
                not_now.click()
                time.sleep(0.1)  # Reducido de 2 a 0.1
            except NoSuchElementException:
                pass
                
        except Exception as e:
            print(f"Error handling security checks: {e}")
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            self.driver = None
