"""
Publicador en grupos de Facebook + union a grupos.

Dos funciones:
  1) join_groups(urls)  -> entra a cada grupo y pulsa "Unirse"/"Join".
  2) post_to_groups(...) -> publica un texto (con imagenes opcionales) en cada
     grupo de la lista, esperando un intervalo ALEATORIO entre publicaciones
     para no caer en el anti-spam de Facebook.

Reutiliza utils.human para tiempos/clicks humanos. Pensado para headless en
Pi / DigitalOcean o Windows, con perfil persistente.

ADVERTENCIA: publicar en masa en grupos puede violar los Terminos de Facebook
y marcarse como spam. Use listas de grupos donde tenga permiso y tiempos
prudentes. Bajo su responsabilidad.
"""
import os

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from utils import human


class GroupPoster:
    """Une a grupos y publica en ellos de forma humana."""

    def __init__(self, driver, post_min_minutes=4, post_max_minutes=12):
        self.driver = driver
        self.post_min_minutes = post_min_minutes
        self.post_max_minutes = post_max_minutes
        self.wait = WebDriverWait(self.driver, 15)

    # ----------------------------------------------------------- unirse a grupos
    def join_groups(self, group_urls):
        """
        Visita cada URL de grupo y pulsa el boton de unirse si existe.
        Devuelve dict {url: 'joined'|'already'|'pending'|'error'}.
        """
        results = {}
        for url in group_urls:
            try:
                print(f"Uniendome a: {url}")
                self.driver.get(url)
                human.pause(2.5, 4.5)
                results[url] = self._click_join_button()
                print(f"  -> {results[url]}")
            except Exception as e:
                print(f"  Error: {e}")
                results[url] = "error"
            human.pause(5.0, 12.0)  # no entrar a 10 grupos de golpe
        return results

    def _click_join_button(self):
        """Pulsa 'Unirse al grupo' / 'Join group'. Devuelve el estado."""
        # Si ya hay un boton de "Compartir/Publicar" o dice "Unido", ya estamos.
        already = [
            "//div[@aria-label='Unido' or @aria-label='Joined']",
            "//span[text()='Unido' or text()='Joined']",
        ]
        for xp in already:
            try:
                self.driver.find_element(By.XPATH, xp)
                return "already"
            except NoSuchElementException:
                continue

        join_xpaths = [
            "//div[@aria-label='Unirse al grupo']",
            "//div[@aria-label='Join group']",
            "//span[text()='Unirse al grupo']/ancestor::div[@role='button'][1]",
            "//span[text()='Join group']/ancestor::div[@role='button'][1]",
            "//span[text()='Unirse']/ancestor::div[@role='button'][1]",
            "//span[text()='Join']/ancestor::div[@role='button'][1]",
        ]
        for xp in join_xpaths:
            try:
                btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
                human.move_and_click(self.driver, btn)
                human.pause(1.5, 3.0)
                # Algunos grupos abren un dialogo con preguntas: lo dejamos pasar.
                return "joined"
            except TimeoutException:
                continue
        return "pending"  # boton no hallado (grupo privado/ya solicitado)

    # --------------------------------------------------------- publicar en grupos
    def post_to_groups(self, group_urls, text, images=None):
        """
        Publica `text` (e `images` opcionales) en cada grupo de la lista.
        Espera un intervalo ALEATORIO entre publicaciones (anti-spam).
        Devuelve dict {url: True|False}.
        """
        results = {}
        total = len(group_urls)
        for i, url in enumerate(group_urls, 1):
            print(f"[{i}/{total}] Publicando en: {url}")
            try:
                results[url] = self.post_to_group(url, text, images)
            except Exception as e:
                print(f"  Error: {e}")
                self._safe_screenshot("group_post_error")
                results[url] = False

            if i < total:
                secs = human.long_pause(self.post_min_minutes, self.post_max_minutes)
                print(f"  Esperando {secs/60:.1f} min antes del siguiente grupo...")
        return results

    def post_to_group(self, group_url, text, images=None):
        """Publica en UN grupo. Devuelve True/False."""
        self.driver.get(group_url)
        human.pause(2.5, 4.5)

        # 1) Abrir el compositor ("Escribe algo..." / "Write something...")
        if not self._open_composer():
            print("  No se pudo abrir el compositor (¿no eres miembro?).")
            return False

        # 2) Escribir el texto
        box = self._get_composer_textbox()
        if not box:
            print("  No se encontro la caja de texto del post.")
            return False
        human.move_and_click(self.driver, box)
        human.type_human(box, text)
        human.pause(0.8, 1.8)

        # 3) Adjuntar imagenes (opcional)
        if images:
            self._attach_images(images)
            human.pause(2.0, 4.0)

        # 4) Publicar
        if not self._click_post_button():
            print("  No se pudo pulsar 'Publicar'.")
            return False

        human.pause(2.5, 4.5)
        print("  ✓ Publicado.")
        return True

    def _open_composer(self):
        """Pulsa el cuadro 'Escribe algo' para abrir el dialogo de publicacion."""
        triggers = [
            "//span[contains(text(),'Escribe algo')]",
            "//span[contains(text(),'Write something')]",
            "//div[contains(@aria-label,'Escribe algo')]",
            "//div[contains(@aria-label,'Write something')]",
            "//div[@role='button'][contains(.,'Crear publicaci')]",
        ]
        for xp in triggers:
            try:
                el = WebDriverWait(self.driver, 6).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
                human.move_and_click(self.driver, el)
                human.pause(1.5, 3.0)
                return True
            except TimeoutException:
                continue
        return False

    def _get_composer_textbox(self):
        """Devuelve el contenteditable del dialogo de publicacion."""
        box_xpaths = [
            "//div[@aria-label='Crea una publicaci' or @aria-label='Create a post']"
            "//div[@role='textbox']",
            "//div[@role='dialog']//div[@contenteditable='true' and @role='textbox']",
            "//div[@contenteditable='true' and @role='textbox']",
        ]
        for xp in box_xpaths:
            try:
                return WebDriverWait(self.driver, 6).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
            except TimeoutException:
                continue
        return None

    def _attach_images(self, images):
        """Sube imagenes al post via el input file oculto."""
        abs_paths = [os.path.abspath(p) for p in images if os.path.exists(p)]
        if not abs_paths:
            return False
        try:
            file_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
            for p in abs_paths:
                file_input.send_keys(p)
                human.pause(0.8, 1.6)
            return True
        except NoSuchElementException:
            # Algunos dialogos requieren pulsar antes el boton "Foto/video".
            for xp in ["//div[@aria-label='Foto/video']", "//div[@aria-label='Photo/video']"]:
                try:
                    btn = self.driver.find_element(By.XPATH, xp)
                    human.move_and_click(self.driver, btn)
                    human.pause(1.0, 2.0)
                    file_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
                    for p in abs_paths:
                        file_input.send_keys(p)
                        human.pause(0.8, 1.6)
                    return True
                except NoSuchElementException:
                    continue
        return False

    def _click_post_button(self):
        """Pulsa el boton 'Publicar' / 'Post' del dialogo."""
        post_xpaths = [
            "//div[@aria-label='Publicar' and @role='button']",
            "//div[@aria-label='Post' and @role='button']",
            "//div[@role='dialog']//span[text()='Publicar']/ancestor::div[@role='button'][1]",
            "//div[@role='dialog']//span[text()='Post']/ancestor::div[@role='button'][1]",
        ]
        for xp in post_xpaths:
            try:
                btn = WebDriverWait(self.driver, 8).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
                human.move_and_click(self.driver, btn)
                return True
            except TimeoutException:
                continue
        return False

    def _safe_screenshot(self, name):
        try:
            os.makedirs("screenshots", exist_ok=True)
            self.driver.save_screenshot(f"screenshots/{name}.png")
        except Exception:
            pass
