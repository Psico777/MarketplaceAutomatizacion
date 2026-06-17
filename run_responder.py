"""
Runner del responder automatico de Messenger (headless / 24-7).

Login -> abre Messenger -> responde los chats no leidos con IA -> espera de 3 a
8 min (aleatorio) -> repite. Pensado para Raspberry Pi 5 / DigitalOcean droplet
(sin pantalla) o Windows.

Uso:
    python run_responder.py                # envia respuestas de verdad
    python run_responder.py --dry-run      # genera pero NO envia (para probar)
    python run_responder.py --rounds 1     # una sola ronda y termina

Recomendado en servidor sin pantalla, definir en .env:
    HEADLESS=True
    CHROME_PROFILE_DIR=/home/USER/.fb_profile   # sesion persistente (no re-2FA)
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.settings import Config
from modules.ai_analyzer import AIImageAnalyzer
from modules.facebook_auth import FacebookAuthenticator
from modules.messenger_responder import MessengerResponder


def main():
    parser = argparse.ArgumentParser(description="Responder automatico de Messenger")
    parser.add_argument("--dry-run", action="store_true",
                        help="Genera respuestas pero NO las envia")
    parser.add_argument("--rounds", type=int, default=None,
                        help="Numero de rondas (por defecto: infinito)")
    args = parser.parse_args()

    Config.validate()

    print("Iniciando sesion en Facebook...")
    auth = FacebookAuthenticator(
        email=Config.FACEBOOK_EMAIL,
        password=Config.FACEBOOK_PASSWORD,
        two_fa_secret=Config.FACEBOOK_2FA_SECRET,
        headless=Config.HEADLESS,
        implicit_wait=Config.IMPLICIT_WAIT,
        profile_dir=Config.CHROME_PROFILE_DIR or None,
        chrome_binary=Config.CHROME_BINARY or None,
    )
    driver = auth.login()
    if not driver:
        print("✗ No se pudo iniciar sesion. Abortando.")
        sys.exit(1)

    ai = AIImageAnalyzer(
        api_key=Config.GEMINI_API_KEY,
        model=Config.AI_MODEL_IMAGE,
        chat_model=Config.AI_MODEL_CHAT,
        max_size=Config.MAX_IMAGE_SIZE,
    )

    responder = MessengerResponder(
        driver=driver,
        ai_analyzer=ai,
        business_context=Config.BUSINESS_CONTEXT,
        min_minutes=Config.RESPONDER_MIN_MINUTES,
        max_minutes=Config.RESPONDER_MAX_MINUTES,
        max_threads_per_round=Config.RESPONDER_MAX_THREADS_PER_ROUND,
        dry_run=args.dry_run,
    )

    try:
        responder.run_forever(max_rounds=args.rounds)
    except KeyboardInterrupt:
        print("\nDetenido por el usuario.")
    finally:
        auth.close()


if __name__ == "__main__":
    main()
