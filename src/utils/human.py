"""
Comportamiento humano para automatización.

Centraliza las pausas, el tipeo y el scroll "como humano". Sustituye los
time.sleep(0.1) fijos del código viejo: ir demasiado rápido y SIEMPRE igual
es la señal #1 que delata un bot y satura la máquina. Aquí todo es aleatorio
y configurable.
"""
import os
import random
import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains


# Permite frenar todo el sistema desde .env (ej. en un Raspberry Pi modesto)
SPEED = float(os.getenv("HUMAN_SPEED", "1.0"))  # >1 = más lento, <1 = más rápido


def pause(a=0.6, b=1.8):
    """Pausa aleatoria estilo humano (segundos)."""
    time.sleep(random.uniform(a, b) * SPEED)


def micro():
    """Pausa muy corta entre micro-acciones (tras un TAB, un click, etc.)."""
    time.sleep(random.uniform(0.15, 0.5) * SPEED)


def long_pause(minutes_min=3, minutes_max=8):
    """
    Espera larga entre ciclos (ej. entre rondas de respuestas).
    Devuelve los segundos esperados por si quieres loguearlos.
    """
    secs = random.uniform(minutes_min * 60, minutes_max * 60) * SPEED
    time.sleep(secs)
    return secs


def type_human(element, text, clear=False):
    """
    Escribe carácter por carácter con micro-pausas variables, como una persona.
    Mucho menos detectable que send_keys(text) de golpe.
    """
    if clear:
        element.clear()
        micro()
    for ch in str(text):
        element.send_keys(ch)
        # la mayoría rápido, de vez en cuando una pausa de "pensar"
        delay = random.uniform(0.03, 0.12)
        if random.random() < 0.04:
            delay += random.uniform(0.2, 0.6)
        time.sleep(delay * SPEED)


def press_tab(driver, times=1):
    """Hace TAB(s) sobre el elemento activo con micro-pausas humanas."""
    for _ in range(times):
        driver.switch_to.active_element.send_keys(Keys.TAB)
        micro()


def human_scroll(driver, amount=None):
    """Scroll suave en varios pasos (no un salto instantáneo)."""
    total = amount if amount is not None else random.randint(300, 800)
    steps = random.randint(4, 8)
    per = total / steps
    for _ in range(steps):
        driver.execute_script("window.scrollBy(0, arguments[0]);", per)
        time.sleep(random.uniform(0.05, 0.2) * SPEED)


def move_and_click(driver, element):
    """Mueve el mouse al elemento y hace click (más natural que .click() directo)."""
    try:
        ActionChains(driver).move_to_element(element).pause(
            random.uniform(0.1, 0.4)
        ).click().perform()
    except Exception:
        # Fallback robusto si ActionChains falla (ej. headless puro)
        element.click()
    micro()


def jitter_chance(probability=0.15):
    """Devuelve True con cierta probabilidad — para acciones humanas ocasionales
    (mirar otra pestaña, hacer scroll sin motivo, etc.)."""
    return random.random() < probability
