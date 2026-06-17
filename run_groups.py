"""
Runner para grupos de Facebook: unirse y/o publicar (headless friendly).

Uso:
    # Unirse a los grupos de FACEBOOK_GROUPS_TO_JOIN (.env)
    python run_groups.py join

    # Publicar un texto en los grupos de FACEBOOK_GROUPS (.env)
    python run_groups.py post --text "GENTE LLEGARON LOS ... <3" \
        --images temp_images/1.jpg temp_images/2.jpg

    # Publicar leyendo el texto desde un archivo
    python run_groups.py post --text-file mensaje.txt

Espera un intervalo ALEATORIO entre publicaciones (anti-spam). Define en .env:
    FACEBOOK_GROUPS=https://facebook.com/groups/AAA,https://facebook.com/groups/BBB
    FACEBOOK_GROUPS_TO_JOIN=https://facebook.com/groups/CCC
    HEADLESS=True
    CHROME_PROFILE_DIR=/home/USER/.fb_profile
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.settings import Config
from modules.facebook_auth import FacebookAuthenticator
from modules.group_poster import GroupPoster


def _login():
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
    return auth, driver


def main():
    parser = argparse.ArgumentParser(description="Unirse / publicar en grupos de Facebook")
    sub = parser.add_subparsers(dest="action", required=True)

    sub.add_parser("join", help="Unirse a FACEBOOK_GROUPS_TO_JOIN")

    p_post = sub.add_parser("post", help="Publicar en FACEBOOK_GROUPS")
    p_post.add_argument("--text", help="Texto de la publicacion")
    p_post.add_argument("--text-file", help="Archivo con el texto de la publicacion")
    p_post.add_argument("--images", nargs="*", default=[], help="Rutas de imagenes")
    p_post.add_argument("--groups", nargs="*", default=None,
                        help="URLs de grupos (sobreescribe FACEBOOK_GROUPS)")

    args = parser.parse_args()

    auth, driver = _login()
    poster = GroupPoster(
        driver,
        post_min_minutes=Config.GROUP_POST_MIN_MINUTES,
        post_max_minutes=Config.GROUP_POST_MAX_MINUTES,
    )

    try:
        if args.action == "join":
            groups = Config.FACEBOOK_GROUPS_TO_JOIN
            if not groups:
                print("No hay grupos en FACEBOOK_GROUPS_TO_JOIN (.env).")
                return
            results = poster.join_groups(groups)
            print("\nResumen union:")
            for url, st in results.items():
                print(f"  {st:>8}  {url}")

        elif args.action == "post":
            text = args.text
            if args.text_file:
                with open(args.text_file, encoding="utf-8") as f:
                    text = f.read().strip()
            if not text:
                print("Falta el texto (--text o --text-file).")
                return
            groups = args.groups if args.groups else Config.FACEBOOK_GROUPS
            if not groups:
                print("No hay grupos en FACEBOOK_GROUPS (.env) ni --groups.")
                return
            results = poster.post_to_groups(groups, text, images=args.images or None)
            ok = sum(1 for v in results.values() if v)
            print(f"\nResumen: {ok}/{len(results)} publicaciones exitosas.")
            for url, v in results.items():
                print(f"  {'OK ' if v else 'FALLO'}  {url}")
    finally:
        auth.close()


if __name__ == "__main__":
    main()
