"""
ELEKA Marketplace - CLI de administracion de licencias
======================================================
Crear / listar / revocar licencias desde la consola, reutilizando la logica
de licensing.py (capa de datos, sin necesidad de FastAPI).

Ejemplos:
    py -3 manage_licenses.py create --plan basic --days 30 --daily-limit 20 --notes "cliente X"
    py -3 manage_licenses.py list
    py -3 manage_licenses.py revoke --key ELEKA-MKT-XXXX-XXXX-XXXX
"""
import sys
import json
import argparse

import licensing


def _cmd_create(args) -> int:
    res = licensing.create_license(
        plan=args.plan, days=args.days,
        daily_limit=args.daily_limit, notes=args.notes,
    )
    print("Licencia creada (guarda la clave, no se vuelve a mostrar):")
    print(f"  key:        {res['key']}")
    print(f"  account_id: {res['account_id']}")
    print(f"  expires_at: {res['expires_at']}")
    return 0


def _cmd_list(_args) -> int:
    rows = licensing.list_licenses()
    if not rows:
        print("No hay licencias registradas.")
        return 0
    print(json.dumps(rows, indent=2, ensure_ascii=False))
    print(f"\nTotal: {len(rows)} licencia(s).")
    return 0


def _cmd_revoke(args) -> int:
    ok = licensing.revoke_license(args.key)
    if ok:
        print("Licencia revocada.")
        return 0
    print("Licencia no encontrada.", file=sys.stderr)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Administracion de licencias de ELEKA Marketplace",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create", help="Crear una licencia nueva")
    p_create.add_argument("--plan", default="basic", help="Nombre del plan (default: basic)")
    p_create.add_argument("--days", type=int, default=30,
                          help="Dias de validez (0 = sin expiracion; default: 30)")
    p_create.add_argument("--daily-limit", dest="daily_limit", type=int,
                          default=licensing.DEFAULT_DAILY_LIMIT,
                          help=f"Limite de publicaciones/dia (default: {licensing.DEFAULT_DAILY_LIMIT})")
    p_create.add_argument("--notes", default="", help="Notas internas (opcional)")
    p_create.set_defaults(func=_cmd_create)

    p_list = sub.add_parser("list", help="Listar licencias (sin claves en claro)")
    p_list.set_defaults(func=_cmd_list)

    p_revoke = sub.add_parser("revoke", help="Revocar una licencia por su clave")
    p_revoke.add_argument("--key", required=True, help="Clave ELEKA-MKT-...")
    p_revoke.set_defaults(func=_cmd_revoke)

    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
