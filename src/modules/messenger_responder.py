"""
Responder automatico de Messenger.

Lee los chats NO LEIDOS de Facebook Messenger, genera una respuesta con la IA
(Gemini, via ai_analyzer.generate_reply) y la envia. Entre rondas espera un
intervalo ALEATORIO de 3 a 8 minutos: ni responde como ametralladora (eso
satura la maquina y delata el bot), ni deja al cliente esperando demasiado.

Pensado para correr 24/7 headless en Raspberry Pi 5 / DigitalOcean droplet, o
en Windows. Usa el perfil persistente de Chrome (CHROME_PROFILE_DIR) para no
re-loguear ni pedir 2FA en cada arranque.

ADVERTENCIA: automatizar Messenger puede violar los Terminos de Facebook.
Uselo bajo su responsabilidad, solo en su propia cuenta/negocio.
"""
import os
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, StaleElementReferenceException,
)

from utils import human


class MessengerResponder:
    """Responde automaticamente los mensajes no leidos con ayuda de la IA."""

    INBOX_URL = "https://www.facebook.com/messages/t/"

    def __init__(self, driver, ai_analyzer, business_context="",
                 min_minutes=3, max_minutes=8, max_threads_per_round=3,
                 dry_run=False):
        """
        Args:
            driver: WebDriver de Selenium ya logueado.
            ai_analyzer: instancia de AIImageAnalyzer (usa .generate_reply()).
            business_context: info del negocio para que la IA responda bien.
            min_minutes / max_minutes: rango aleatorio de espera entre rondas.
            max_threads_per_round: cuantos hilos responder como mucho por ronda.
            dry_run: si True, genera la respuesta pero NO la envia (para probar).
        """
        self.driver = driver
        self.ai = ai_analyzer
        self.business_context = business_context
        self.min_minutes = min_minutes
        self.max_minutes = max_minutes
        self.max_threads_per_round = max_threads_per_round
        self.dry_run = dry_run
        self.wait = WebDriverWait(self.driver, 15)
        # Evita responder dos veces el mismo texto del mismo hilo en una sesion.
        self._answered = {}

    # ------------------------------------------------------------------ ciclo
    def run_forever(self, max_rounds=None):
        """
        Bucle principal. Cada ronda: abre el inbox, responde los no leidos y
        espera un tiempo ALEATORIO antes de la siguiente ronda.

        Args:
            max_rounds: limite de rondas (None = infinito). Util para pruebas.
        """
        print("=" * 60)
        print("Responder de Messenger iniciado")
        print(f"  Intervalo aleatorio: {self.min_minutes}-{self.max_minutes} min")
        print(f"  Hilos por ronda: {self.max_threads_per_round}")
        print(f"  Modo: {'DRY-RUN (no envia)' if self.dry_run else 'ENVIO REAL'}")
        print("=" * 60)

        rounds = 0
        while max_rounds is None or rounds < max_rounds:
            rounds += 1
            try:
                answered = self.run_once()
                print(f"[Ronda {rounds}] {answered} respuesta(s) enviada(s).")
            except Exception as e:
                print(f"[Ronda {rounds}] Error en la ronda: {e}")
                self._safe_screenshot("responder_error")

            secs = human.long_pause(self.min_minutes, self.max_minutes)
            print(f"  Esperando {secs/60:.1f} min hasta la siguiente ronda...")

    def run_once(self):
        """Procesa una ronda de chats no leidos. Devuelve cuantos respondio."""
        self.driver.get(self.INBOX_URL)
        human.pause(2.5, 4.5)

        unread = self._find_unread_threads()
        if not unread:
            print("  No hay mensajes no leidos.")
            return 0

        print(f"  {len(unread)} hilo(s) no leido(s). Respondiendo hasta "
              f"{self.max_threads_per_round}...")

        answered = 0
        for thread in unread[: self.max_threads_per_round]:
            try:
                if self._handle_thread(thread):
                    answered += 1
                    # pausa humana entre responder un chat y el siguiente
                    human.pause(4.0, 9.0)
            except StaleElementReferenceException:
                # el DOM cambio al abrir el chat; seguimos con el siguiente
                continue
            except Exception as e:
                print(f"    Error en un hilo: {e}")
                continue
        return answered

    # ------------------------------------------------------------ inbox/hilos
    def _find_unread_threads(self):
        """
        Devuelve la lista de elementos <a> de hilos NO leidos. Facebook marca
        los no leidos con texto en negrita (aria-label suele incluir
        'sin leer' / 'unread'), pero como la UI cambia mucho probamos varias
        senales y caemos a una heuristica de estilo de fuente.
        """
        candidates = []
        try:
            self.wait.until(EC.presence_of_element_located(
                (By.XPATH, "//div[@role='grid'] | //div[@aria-label='Chats']")
            ))
        except TimeoutException:
            pass
        human.pause(1.0, 2.0)

        # 1) por aria-label (idioma ES/EN)
        xpaths = [
            "//a[contains(@aria-label,'sin leer')]",
            "//a[contains(@aria-label,'Unread') or contains(@aria-label,'unread')]",
            "//div[@aria-label='Chats']//a[@role='link']",
            "//div[@role='grid']//a[@role='link']",
        ]
        seen_hrefs = set()
        for xp in xpaths:
            try:
                for el in self.driver.find_elements(By.XPATH, xp):
                    href = el.get_attribute("href") or ""
                    if "/messages/t/" not in href or href in seen_hrefs:
                        continue
                    if "sin leer" in xp or "nread" in xp or self._looks_unread(el):
                        seen_hrefs.add(href)
                        candidates.append(el)
            except (NoSuchElementException, StaleElementReferenceException):
                continue
            if candidates:
                break
        return candidates

    def _looks_unread(self, link_el):
        """Heuristica: un hilo no leido suele venir en negrita (font-weight)."""
        try:
            spans = link_el.find_elements(By.XPATH, ".//span")
            for sp in spans[:6]:
                weight = sp.value_of_css_property("font-weight")
                if weight and weight.isdigit() and int(weight) >= 600:
                    return True
        except (StaleElementReferenceException, NoSuchElementException):
            pass
        return False

    def _handle_thread(self, thread_link):
        """Abre un hilo, lee el ultimo mensaje del cliente, responde."""
        href = thread_link.get_attribute("href")
        human.move_and_click(self.driver, thread_link)
        human.pause(2.0, 4.0)

        history = self._read_visible_messages()
        if not history:
            print("    Hilo sin mensajes legibles, se omite.")
            return False

        last_msg = history[-1]
        # Si lo ultimo lo escribimos nosotros, no hay nada que responder.
        if self._answered.get(href) == last_msg:
            return False

        print(f"    Cliente: {last_msg[:60]}")
        reply = self.ai.generate_reply(
            last_msg, business_context=self.business_context, history=history
        )
        print(f"    IA -> {reply[:80]}")

        if self.dry_run:
            self._answered[href] = last_msg
            return True

        if self._send_message(reply):
            self._answered[href] = last_msg
            return True
        return False

    def _read_visible_messages(self, limit=12):
        """
        Devuelve los ultimos mensajes visibles del hilo como lista de strings.
        Usa los aria-label de los grupos de mensajes (robusto a cambios de clase).
        """
        msgs = []
        selectors = [
            "//div[@role='row']//div[@dir='auto']",
            "//div[contains(@aria-label,'Mensajes')]//div[@dir='auto']",
            "//div[@aria-label='Mensajes']//div[@dir='auto']",
        ]
        for xp in selectors:
            try:
                els = self.driver.find_elements(By.XPATH, xp)
                texts = [e.text.strip() for e in els if e.text and e.text.strip()]
                if texts:
                    msgs = texts
                    break
            except (NoSuchElementException, StaleElementReferenceException):
                continue
        return msgs[-limit:]

    def _send_message(self, text):
        """Escribe en la caja de mensaje y envia con Enter (tipeo humano)."""
        box_xpaths = [
            "//div[@aria-label='Mensaje' and @contenteditable='true']",
            "//div[@aria-label='Message' and @contenteditable='true']",
            "//div[@role='textbox' and @contenteditable='true']",
        ]
        box = None
        for xp in box_xpaths:
            try:
                box = WebDriverWait(self.driver, 6).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
                break
            except TimeoutException:
                continue
        if not box:
            print("    No se encontro la caja de mensaje.")
            self._safe_screenshot("no_message_box")
            return False

        human.move_and_click(self.driver, box)
        human.type_human(box, text)
        human.micro()
        box.send_keys(Keys.ENTER)
        human.pause(1.0, 2.2)
        return True

    # ------------------------------------------------------------------ util
    def _safe_screenshot(self, name):
        try:
            os.makedirs("screenshots", exist_ok=True)
            self.driver.save_screenshot(f"screenshots/{name}.png")
        except Exception:
            pass
