"""
Facebook Authentication Module
Login a Facebook con soporte 2FA usando Selenium.

Mejoras vs versión anterior:
- Perfil de Chrome PERSISTENTE (user-data-dir): logueas una vez y la sesión
  sobrevive entre ejecuciones -> el responder 24/7 no pide 2FA cada arranque.
- Headless "new" opcional para servidor sin pantalla (Raspberry Pi / DO droplet).
- Binario de Chrome y chromedriver configurables (útil en ARM / headless).
- Delays humanos (no 0.1-0.2s fijos) y manejo de errores explícito.
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

from utils import human


class FacebookAuthenticator:
    """Maneja el login a Facebook con soporte 2FA y sesión persistente."""

    def __init__(self, email, password, two_fa_secret=None, headless=False,
                 implicit_wait=10, twofa_callback=None, profile_dir=None,
                 chrome_binary=None):
        """
        Args:
            email, password: credenciales de Facebook.
            two_fa_secret: secreto TOTP (opcional; si no, aprobación manual).
            headless: True para servidor sin pantalla (Pi / DO).
            implicit_wait: espera implícita de Selenium (s).
            twofa_callback: callback para confirmar 2FA desde GUI.
            profile_dir: carpeta del perfil persistente de Chrome. Si se indica,
                         la sesión se guarda y NO hay que re-loguear cada vez.
            chrome_binary: ruta al binario de Chrome (útil en ARM / headless).
        """
        self.email = email
        self.password = password
        self.two_fa_secret = two_fa_secret
        self.headless = headless
        self.implicit_wait = implicit_wait
        self.twofa_callback = twofa_callback
        self.profile_dir = profile_dir or os.getenv("CHROME_PROFILE_DIR")
        self.chrome_binary = chrome_binary or os.getenv("CHROME_BINARY")
        self.driver = None

    def setup_driver(self):
        """Configura el Chrome WebDriver."""
        opts = Options()

        if self.headless:
            # "new" mantiene la UI moderna de Facebook en headless
            opts.add_argument("--headless=new")

        if self.chrome_binary:
            opts.binary_location = self.chrome_binary

        # Perfil persistente -> conserva la sesión (login + cookies) entre runs
        if self.profile_dir:
            os.makedirs(self.profile_dir, exist_ok=True)
            opts.add_argument(f"--user-data-dir={self.profile_dir}")

        # Opciones esenciales (servidor / contenedor / Pi)
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--disable-software-rasterizer")
        opts.add_argument("--disable-extensions")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )
        opts.add_argument("--force-device-scale-factor=1.0")

        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.media_stream_camera": 2,
            "profile.default_content_setting_values.media_stream_mic": 2,
            "profile.default_content_setting_values.geolocation": 2,
        }
        opts.add_experimental_option("prefs", prefs)
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)

        # ⚠️ Automatizar Facebook puede violar sus Términos. Úsalo bajo tu
        # responsabilidad y solo en tu propia cuenta/negocio.
        driver_path = self._resolve_driver_path()
        service = Service(driver_path)
        self.driver = webdriver.Chrome(service=service, options=opts)
        self.driver.implicitly_wait(self.implicit_wait)
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        return self.driver

    def _resolve_driver_path(self):
        """Devuelve la ruta real al binario de chromedriver."""
        # Permite fijarlo por env (ej. ruta del chromedriver de ARM en el Pi)
        env_path = os.getenv("CHROMEDRIVER_PATH")
        if env_path and os.path.exists(env_path):
            return env_path
        path = ChromeDriverManager().install()
        # webdriver_manager a veces apunta al NOTICES en vez del binario
        if not path.endswith("chromedriver") and not path.endswith("chromedriver.exe"):
            d = os.path.dirname(path)
            for f in os.listdir(d):
                if f in ("chromedriver", "chromedriver.exe"):
                    return os.path.join(d, f)
        return path

    def login(self, url="https://www.facebook.com/"):
        """Hace login. Devuelve el driver si tuvo éxito, None si falló."""
        try:
            if not self.driver:
                self.setup_driver()

            print("Navegando a Facebook...")
            self.driver.get(url)
            human.pause(1.0, 2.5)

            if self._is_logged_in():
                print("Sesión ya activa (perfil persistente).")
                return self.driver

            print("Ingresando email...")
            email_field = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            human.type_human(email_field, self.email, clear=True)

            print("Ingresando contraseña...")
            pass_field = self.driver.find_element(By.ID, "pass")
            human.type_human(pass_field, self.password, clear=True)

            print("Click en iniciar sesión...")
            human.move_and_click(self.driver, self.driver.find_element(By.NAME, "login"))
            human.pause(2.0, 4.0)

            os.makedirs("screenshots", exist_ok=True)
            self.driver.save_screenshot("screenshots/after_login.png")

            if self._check_2fa_required():
                print("2FA requerido...")
                if not self._handle_2fa():
                    print("Falló el 2FA")
                    return None

            self._handle_security_checks()

            if self._is_logged_in():
                print("✓ Login exitoso!")
                return self.driver

            print("✗ Login no completado")
            print(f"  URL actual: {self.driver.current_url}")
            self.driver.save_screenshot("screenshots/login_failed.png")
            return None

        except TimeoutException:
            print("✗ Timeout esperando los campos de login (¿UI distinta?)")
            return None
        except Exception as e:
            print(f"✗ Error durante el login: {e}")
            return None

    def _is_logged_in(self):
        """
        Verifica sesión activa. Mejor señal que role='navigation' (que también
        existe deslogueado): buscamos elementos exclusivos de sesión iniciada.
        """
        url = self.driver.current_url
        if "login" in url or "checkpoint" in url:
            return False
        signals = [
            "//div[@aria-label='Tu perfil']",
            "//div[@aria-label='Your profile']",
            "//a[@aria-label='Inicio' or @aria-label='Home']",
            "//div[@role='banner']//div[@aria-label]",
        ]
        for xp in signals:
            try:
                self.driver.find_element(By.XPATH, xp)
                return True
            except NoSuchElementException:
                continue
        return False

    def _check_2fa_required(self):
        """Detecta si Facebook pide 2FA."""
        url = self.driver.current_url
        if "two_step_verification" in url or "checkpoint" in url:
            return True
        try:
            self.driver.find_element(By.ID, "approvals_code")
            return True
        except NoSuchElementException:
            return False

    def _handle_2fa(self):
        """Maneja el 2FA (TOTP automático o aprobación manual en celular)."""
        try:
            # Sin secret válido -> aprobación manual
            if not self.two_fa_secret or len(self.two_fa_secret) < 16:
                print("\n" + "=" * 60)
                print("🔐 2FA REQUERIDO - aprueba en tu celular")
                print("=" * 60)
                if self.twofa_callback:
                    try:
                        if not self.twofa_callback():
                            print("✗ Usuario canceló 2FA")
                            return False
                    except Exception as e:
                        print(f"Error en callback 2FA: {e}")
                        return False
                else:
                    try:
                        input(">>> ENTER cuando estés dentro de Facebook: ")
                    except (KeyboardInterrupt, EOFError):
                        # En background (sin TTY) esperamos a que apruebe en el cel
                        print("Sin TTY: esperando 60s a la aprobación móvil...")
                        time.sleep(60)
                human.pause(1.5, 3.0)
                if self._is_logged_in():
                    print("✓ 2FA completado!")
                    return True
                human.pause(2.0, 3.0)
                return self._is_logged_in()

            # Con secret -> TOTP automático
            code = pyotp.TOTP(self.two_fa_secret).now()
            print(f"Código 2FA generado: {code}")
            code_field = self.driver.find_element(By.ID, "approvals_code")
            human.type_human(code_field, code, clear=True)
            human.move_and_click(
                self.driver, self.driver.find_element(By.ID, "checkpointSubmitButton")
            )
            human.pause(2.0, 4.0)
            try:
                btn = self.driver.find_element(
                    By.XPATH, "//button[contains(text(),'Not Now') or contains(text(),'Ahora no')]"
                )
                human.move_and_click(self.driver, btn)
            except NoSuchElementException:
                pass
            return True

        except Exception as e:
            print(f"Error manejando 2FA: {e}")
            return False

    def _handle_security_checks(self):
        """Cierra popups de 'Guardar sesión' / notificaciones."""
        for xp in [
            "//button[contains(text(),'Not Now') or contains(text(),'Ahora no')]",
            "//button[contains(text(),'Block') or contains(text(),'Bloquear')]",
        ]:
            try:
                btn = WebDriverWait(self.driver, 4).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
                human.move_and_click(self.driver, btn)
            except TimeoutException:
                pass

    def close(self):
        """Cierra el navegador."""
        if self.driver:
            self.driver.quit()
            self.driver = None
