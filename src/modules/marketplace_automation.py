"""
Facebook Marketplace Automation Module
Crea publicaciones de forma RESILIENTE: detecta los campos por aria-label /
placeholder / label con varios fallbacks (en vez de contar TABs fijos), elige
la categoria de forma dinamica y usa pausas humanas. Mantiene un fallback por
TAB como ultimo recurso para degradar con gracia si FB cambia el DOM.
"""
import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys

from modules.human import human_delay, human_type


class MarketplaceAutomation:
    """Automatiza operaciones de Facebook Marketplace."""

    def __init__(self, driver, human_min=0.4, human_max=1.2):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 15)
        self.human_min = human_min
        self.human_max = human_max

    def _pause(self):
        human_delay(self.human_min, self.human_max)

    # ------------------------------------------------------------------
    #  Localizador resiliente de campos
    # ------------------------------------------------------------------
    def _find(self, strategies, timeout=6, clickable=False):
        """Intenta varias estrategias (By, valor) y devuelve el primer elemento."""
        cond = EC.element_to_be_clickable if clickable else EC.presence_of_element_located
        for by, value in strategies:
            try:
                return WebDriverWait(self.driver, timeout).until(cond((by, value)))
            except TimeoutException:
                continue
        return None

    def _labels(self, *names):
        """Genera estrategias de busqueda para inputs/textarea por aria-label/placeholder."""
        strategies = []
        for n in names:
            strategies += [
                (By.XPATH, f"//input[@aria-label='{n}']"),
                (By.XPATH, f"//textarea[@aria-label='{n}']"),
                (By.XPATH, f"//input[@placeholder='{n}']"),
                (By.XPATH, f"//textarea[@placeholder='{n}']"),
                (By.XPATH, f"//label[contains(., '{n}')]//input"),
                (By.XPATH, f"//label[contains(., '{n}')]//textarea"),
            ]
        return strategies

    # ------------------------------------------------------------------
    #  Crear publicacion
    # ------------------------------------------------------------------
    def create_listing(self, title, description, price, category=None,
                       condition='Nuevo', images=None, tags=None, location=None):
        images = images or []
        tags = tags or []
        try:
            print("Abriendo pagina de crear publicacion...")
            self.driver.get('https://www.facebook.com/marketplace/create/item')
            try:
                self.driver.maximize_window()
            except Exception:
                pass
            human_delay(1.5, 2.5)
            os.makedirs('screenshots', exist_ok=True)
            self.driver.save_screenshot('screenshots/marketplace_create.png')

            # 1) Imagenes primero
            print("Subiendo imagenes...")
            if not self._upload_images(images):
                print("Aviso: la subida de imagenes pudo fallar, continuando...")
            self._pause()

            # 2) Titulo
            print("Escribiendo titulo...")
            if not self._fill_title(title):
                print("No se pudo escribir el titulo")
                return False

            # 3) Precio
            print("Escribiendo precio...")
            self._fill_price(price)
            self._pause()

            # 4) Categoria (dinamica)
            if category:
                print(f"Seleccionando categoria: {category}")
                self._select_combo(['Categoria', 'Category'], category)
                self._pause()

            # 5) Estado / condicion
            print(f"Estado: {condition}")
            self._select_combo(['Estado', 'Condition'], condition)
            self._pause()

            # 6) Descripcion
            print("Escribiendo descripcion...")
            self._fill_description(description)
            self._pause()

            # 7) Tags / etiquetas (opcional, si el campo existe)
            self._add_tags(['remate', 'oferta'] + list(tags[:6]))

            # 8) Siguiente -> Publicar
            print("Publicando...")
            self._click_button(['Siguiente', 'Next'])
            human_delay(1.0, 2.0)
            published = self._click_button(['Publicar', 'Publish'])

            human_delay(1.5, 2.5)
            self.driver.save_screenshot('screenshots/listing_published.png')
            print("Publicacion completada!" if published else "No se confirmo el boton Publicar")
            return True

        except Exception as e:
            print(f"Error creando publicacion: {e}")
            import traceback
            traceback.print_exc()
            try:
                self.driver.save_screenshot('screenshots/listing_error.png')
            except Exception:
                pass
            return False

    # ------------------------------------------------------------------
    #  Pasos individuales (con fallback)
    # ------------------------------------------------------------------
    def _upload_images(self, image_paths):
        try:
            file_inputs = self.driver.find_elements(By.XPATH, "//input[@type='file' and @accept]")
            if not file_inputs:
                file_inputs = self.driver.find_elements(By.XPATH, "//input[@type='file']")
            if not file_inputs:
                print("No se encontro input de archivos")
                return False
            file_input = file_inputs[0]
            abs_paths = [os.path.abspath(p) for p in image_paths if os.path.exists(p)]
            if not abs_paths:
                print("No hay rutas de imagen validas")
                return False
            # send_keys con varias rutas separadas por \n sube todas a la vez
            file_input.send_keys("\n".join(abs_paths))
            human_delay(1.0, 2.0)
            print(f"  {len(abs_paths)} imagen(es) enviadas")
            return True
        except Exception as e:
            print(f"Error subiendo imagenes: {e}")
            return False

    def _fill_title(self, title):
        field = self._find(self._labels('Titulo', 'Título', 'Title'), timeout=8)
        if field:
            try:
                field.click()
                self._pause()
                field.send_keys(Keys.CONTROL, 'a')
                field.send_keys(title)
                val = field.get_attribute('value') or ''
                if val.strip():
                    print(f"  Titulo OK: {val[:30]}...")
                    return True
            except Exception as e:
                print(f"  Error escribiendo titulo (directo): {e}")
        # Fallback: metodo por TAB desde la subida de imagenes
        return self._fill_title_tab_fallback(title)

    def _fill_title_tab_fallback(self, title):
        try:
            print("  Fallback TAB para titulo...")
            for _ in range(14):
                self.driver.switch_to.active_element.send_keys(Keys.TAB)
                time.sleep(0.1)
            active = self.driver.switch_to.active_element
            active.send_keys(title)
            return bool((active.get_attribute('value') or '').strip())
        except Exception as e:
            print(f"  Fallback de titulo fallo: {e}")
            return False

    def _fill_price(self, price):
        field = self._find(self._labels('Precio', 'Price'), timeout=5)
        if field:
            try:
                field.click()
                field.send_keys(Keys.CONTROL, 'a')
                field.send_keys(str(price))
                return True
            except Exception:
                pass
        # Fallback: TAB desde el titulo
        try:
            active = self.driver.switch_to.active_element
            active.send_keys(Keys.TAB)
            time.sleep(0.2)
            active = self.driver.switch_to.active_element
            active.send_keys(str(price))
            return True
        except Exception as e:
            print(f"  No se pudo escribir el precio: {e}")
            return False

    def _fill_description(self, description):
        field = self._find(
            self._labels('Descripcion', 'Descripción', 'Description') +
            [(By.XPATH, "//div[@contenteditable='true' and @role='textbox']"),
             (By.XPATH, "//textarea")],
            timeout=6,
        )
        if not field:
            print("  No se encontro el campo de descripcion")
            return False
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", field)
            field.click()
            self._pause()
            field.send_keys(description)
            return True
        except Exception as e:
            print(f"  Error escribiendo descripcion: {e}")
            return False

    def _select_combo(self, label_names, value):
        """Abre un combo (Categoria/Estado) y elige la opcion por texto visible."""
        combo = self._find(
            [(By.XPATH, f"//label[contains(., '{n}')]") for n in label_names] +
            [(By.XPATH, f"//*[@aria-label='{n}']") for n in label_names],
            timeout=5, clickable=True,
        )
        if not combo:
            print(f"  Combo no encontrado: {label_names}")
            return False
        try:
            combo.click()
            self._pause()
            # buscar la opcion por texto exacto o parcial
            option = self._find(
                [(By.XPATH, f"//span[normalize-space(text())='{value}']"),
                 (By.XPATH, f"//div[@role='option']//span[contains(text(), '{value}')]"),
                 (By.XPATH, f"//*[@role='menuitemradio'][contains(., '{value}')]"),
                 (By.XPATH, f"//span[contains(text(), '{value}')]")],
                timeout=4, clickable=True,
            )
            if option:
                option.click()
                self._pause()
                return True
            # fallback: escribir y enter
            active = self.driver.switch_to.active_element
            human_type(active, value)
            active.send_keys(Keys.ENTER)
            return True
        except Exception as e:
            print(f"  No se pudo seleccionar '{value}': {e}")
            return False

    def _add_tags(self, tags):
        field = self._find(self._labels('Etiquetas', 'Tags'), timeout=3)
        if not field:
            return  # campo de tags es opcional
        for tag in tags:
            try:
                field.send_keys(tag)
                time.sleep(0.15)
                field.send_keys(Keys.ENTER)
                time.sleep(0.15)
            except Exception:
                break

    def _click_button(self, texts):
        for t in texts:
            btn = self._find(
                [(By.XPATH, f"//div[@role='button'][.//span[text()='{t}']]"),
                 (By.XPATH, f"//div[@role='button'][contains(., '{t}')]"),
                 (By.XPATH, f"//span[text()='{t}']/ancestor::div[@role='button'][1]"),
                 (By.XPATH, f"//button[contains(., '{t}')]")],
                timeout=6, clickable=True,
            )
            if btn:
                try:
                    btn.click()
                    return True
                except Exception:
                    try:
                        self.driver.execute_script("arguments[0].click();", btn)
                        return True
                    except Exception:
                        continue
        print(f"  No se encontro el boton: {texts}")
        return False

    # ------------------------------------------------------------------
    #  Gestion de publicaciones existentes
    # ------------------------------------------------------------------
    def get_my_listings(self):
        try:
            from config.settings import Config
            print("Abriendo tus publicaciones...")
            self.driver.get(Config.MARKETPLACE_SELLING_URL)
            human_delay(3.0, 5.0)
            listings = []
            for element in self.driver.find_elements(By.XPATH, "//a[contains(@href, '/marketplace/item/')]"):
                href = element.get_attribute('href')
                if href and href not in listings:
                    listings.append(href)
            print(f"Encontradas {len(listings)} publicaciones")
            return listings
        except Exception as e:
            print(f"Error obteniendo publicaciones: {e}")
            return []

    def delete_listing(self, listing_url):
        try:
            self.driver.get(listing_url)
            human_delay(2.0, 3.0)
            self._click_button(['More', 'Mas', 'Más'])
            human_delay(1.0, 2.0)
            self._click_button(['Delete', 'Eliminar'])
            human_delay(1.0, 2.0)
            self._click_button(['Delete', 'Eliminar', 'Confirm', 'Confirmar'])
            human_delay(1.0, 2.0)
            return True
        except Exception as e:
            print(f"Error eliminando publicacion: {e}")
            return False
