"""
Facebook Authentication Module
Login con soporte 2FA y SESION PERSISTENTE (perfil de Chrome guardado),
para no re-loguear ni pedir 2FA en cada corrida.
"""
import os
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

from modules.human import human_delay


class FacebookAuthenticator:
    """Maneja la autenticacion en Facebook con 2FA y perfil persistente."""

    def __init__(self, email, password, two_fa_secret=None, headless=False,
                 implicit_wait=10, twofa_callback=None, user_data_dir=None):
        self.email = email
        self.password = password
        self.two_fa_secret = two_fa_secret
        self.headless = headless
        self.implicit_wait = implicit_wait
        self.twofa_callback = twofa_callback
        self.user_data_dir = user_data_dir
        self.driver = None

    def setup_driver(self):
        """Configura Chrome WebDriver (con perfil persistente si se indico)."""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument('--headless=new')

        # Perfil persistente: mantiene cookies/sesion entre corridas
        if self.user_data_dir:
            os.makedirs(self.user_data_dir, exist_ok=True)
            chrome_options.add_argument(f'--user-data-dir={self.user_data_dir}')

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
        chrome_options.add_argument('--force-device-scale-factor=1.0')

        prefs = {
            'profile.default_content_setting_values.notifications': 2,
            'profile.default_content_setting_values.media_stream_camera': 2,
            'profile.default_content_setting_values.media_stream_mic': 2,
            'profile.default_content_setting_values.geolocation': 2,
        }
        chrome_options.add_experimental_option('prefs', prefs)

        # NOTA: automatizar Facebook puede violar sus Terminos de Servicio.
        # Usa esto solo con TU cuenta y TUS productos, bajo tu propio riesgo.
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        driver_path = ChromeDriverManager().install()
        if driver_path.endswith('THIRD_PARTY_NOTICES.chromedriver') or not driver_path.endswith('chromedriver'):
            driver_dir = os.path.dirname(driver_path)
            for file in os.listdir(driver_dir):
                if file in ('chromedriver', 'chromedriver.exe'):
                    driver_path = os.path.join(driver_dir, file)
                    break

        service = Service(driver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(self.implicit_wait)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return self.driver

    def login(self, url='https://www.facebook.com/'):
        """Inicia sesion. Si el perfil ya tiene sesion, no vuelve a loguear."""
        try:
            if not self.driver:
                self.setup_driver()

            print("Navegando a Facebook...")
            self.driver.get(url)
            human_delay(1.0, 2.0)

            # Con perfil persistente, normalmente ya estamos dentro
            if self._is_logged_in():
                print("Ya hay sesion iniciada (perfil persistente)!")
                return self.driver

            # Si no hay campos de login (otra pantalla), intentar igual
            print("Ingresando email...")
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            email_field.clear()
            email_field.send_keys(self.email)
            human_delay(0.4, 1.0)

            print("Ingresando password...")
            password_field = self.driver.find_element(By.ID, "pass")
            password_field.clear()
            password_field.send_keys(self.password)
            human_delay(0.4, 1.0)

            print("Click en login...")
            self.driver.find_element(By.NAME, "login").click()
            human_delay(2.0, 3.5)

            os.makedirs('screenshots', exist_ok=True)
            self.driver.save_screenshot('screenshots/after_login.png')

            if self._check_2fa_required():
                print("2FA requerido...")
                if not self._handle_2fa():
                    print("Fallo el 2FA")
                    return None

            self._handle_security_checks()

            if self._is_logged_in():
                print("Login exitoso!")
                return self.driver
            else:
                print("Login fallido - no se detecto sesion")
                print(f"URL actual: {self.driver.current_url}")
                self.driver.save_screenshot('screenshots/login_failed.png')
                return None

        except Exception as e:
            print(f"Error durante el login: {e}")
            return None

    def _is_logged_in(self):
        try:
            self.driver.find_element(By.XPATH, "//div[@role='navigation']")
            return True
        except NoSuchElementException:
            return False

    def _check_2fa_required(self):
        try:
            if 'two_step_verification' in self.driver.current_url or 'checkpoint' in self.driver.current_url:
                return True
            self.driver.find_element(By.ID, "approvals_code")
            return True
        except NoSuchElementException:
            return False

    def _handle_2fa(self):
        try:
            # Sin secret valido -> aprobacion manual desde el celular
            if not self.two_fa_secret or len(self.two_fa_secret) < 16:
                print("\n" + "=" * 60)
                print("2FA REQUERIDO - Aprueba en tu celular")
                print("=" * 60)
                if self.twofa_callback:
                    try:
                        if not self.twofa_callback():
                            print("Usuario cancelo el 2FA")
                            return False
                    except Exception as e:
                        print(f"Error en 2FA: {e}")
                        return False
                else:
                    try:
                        input(">>> Presiona ENTER cuando estes dentro de Facebook: ")
                    except (KeyboardInterrupt, EOFError):
                        print("Esperando 60s para aprobacion manual...")
                        time.sleep(60)

                human_delay(1.0, 2.0)
                if self._is_logged_in():
                    print("2FA completado!")
                    return True
                human_delay(2.0, 3.0)
                return self._is_logged_in()

            # 2FA automatico via TOTP
            totp = pyotp.TOTP(self.two_fa_secret)
            code = totp.now()
            print(f"Codigo 2FA generado: {code}")
            code_field = self.driver.find_element(By.ID, "approvals_code")
            code_field.clear()
            code_field.send_keys(code)
            self.driver.find_element(By.ID, "checkpointSubmitButton").click()
            human_delay(2.0, 3.0)

            try:
                self.driver.find_element(
                    By.XPATH, "//button[contains(text(), 'Not Now') or contains(text(), 'Don')]"
                ).click()
                human_delay(0.5, 1.0)
            except NoSuchElementException:
                pass
            return True

        except Exception as e:
            print(f"Error manejando 2FA: {e}")
            return False

    def _handle_security_checks(self):
        try:
            try:
                not_now = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Not Now')]"))
                )
                not_now.click()
                human_delay(0.5, 1.0)
            except TimeoutException:
                pass
            try:
                self.driver.find_element(
                    By.XPATH, "//button[contains(text(), 'Not Now') or contains(text(), 'Block')]"
                ).click()
                human_delay(0.5, 1.0)
            except NoSuchElementException:
                pass
        except Exception as e:
            print(f"Error en chequeos de seguridad: {e}")

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
