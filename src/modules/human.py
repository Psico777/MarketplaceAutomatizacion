"""
Comportamiento humano para reducir el riesgo de deteccion/baneo.

Estas utilidades NO evaden controles de nadie mas: solo espacian las acciones
de TU propia cuenta para que el ritmo no parezca el de un bot. Usalo solo en
cuentas y publicaciones propias.
"""
import time
import random


def human_delay(min_s=0.4, max_s=1.2):
    """Pausa aleatoria corta entre acciones de un mismo formulario."""
    time.sleep(random.uniform(min_s, max_s))


def human_gap(min_s=25, max_s=70, on_tick=None):
    """
    Pausa larga (aleatoria) entre una publicacion y la siguiente.

    Args:
        min_s, max_s: rango en segundos.
        on_tick(callable): se llama cada segundo con (restante, total) para
                           poder mostrar el conteo en la GUI.
    """
    total = int(random.uniform(min_s, max_s))
    for remaining in range(total, 0, -1):
        if on_tick:
            try:
                on_tick(remaining, total)
            except Exception:
                pass
        time.sleep(1)
    return total


def human_type(element, text, min_s=0.02, max_s=0.09):
    """Escribe caracter por caracter con micro-pausas (como una persona)."""
    for ch in str(text):
        element.send_keys(ch)
        time.sleep(random.uniform(min_s, max_s))
