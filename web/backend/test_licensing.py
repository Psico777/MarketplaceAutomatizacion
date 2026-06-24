"""
ELEKA Marketplace - Autotest de la API de licencias
===================================================
Prueba la capa de datos de licensing.py SIN depender de FastAPI:
  - crear una licencia
  - validar (caso ok)
  - validar una clave inexistente -> not_found
  - validar una revocada -> revoked
  - validar una expirada -> expired
  - binding de machine_id: fijar y luego mismatch -> machine_mismatch

Usa una BD temporal aislada para no tocar licenses.db de produccion.
Imprime PASS/FAIL por caso y devuelve codigo de salida != 0 si algo falla.
"""
import sys
import tempfile
import datetime
import sqlite3
from pathlib import Path

import licensing


_RESULTS = []


def check(name: str, condition: bool, detail: str = "") -> None:
    estado = "PASS" if condition else "FAIL"
    extra = f" -> {detail}" if detail else ""
    print(f"[{estado}] {name}{extra}")
    _RESULTS.append(condition)


def _insert_expired_license() -> str:
    """Inserta directamente una licencia ya expirada y devuelve su clave."""
    key = licensing.generate_key()
    created = licensing._now() - datetime.timedelta(days=40)
    expires = licensing._now() - datetime.timedelta(days=1)  # ayer
    with sqlite3.connect(str(licensing.DB_PATH)) as conn:
        conn.execute(
            """
            INSERT INTO licenses
                (key_hash, account_id, plan, status, machine_id,
                 created_at, expires_at, daily_limit, notes)
            VALUES (?, ?, ?, 'active', NULL, ?, ?, ?, '')
            """,
            (licensing._key_hash(key), licensing.account_id_for(key), "basic",
             licensing._iso(created), licensing._iso(expires), 20),
        )
        conn.commit()
    return key


def run() -> int:
    # --- BD temporal aislada ---
    tmpdir = tempfile.mkdtemp(prefix="eleka_lic_test_")
    licensing.DB_PATH = Path(tmpdir) / "licenses_test.db"
    licensing.init_db()

    print("== Autotest API de licencias ELEKA ==")
    print(f"BD temporal: {licensing.DB_PATH}\n")

    # --- formato de clave ---
    key_sample = licensing.generate_key()
    import re
    fmt_ok = bool(re.fullmatch(r"ELEKA-MKT-[A-HJ-NP-Z2-9]{4}-[A-HJ-NP-Z2-9]{4}-[A-HJ-NP-Z2-9]{4}", key_sample))
    check("formato de clave ELEKA-MKT-XXXX-XXXX-XXXX (sin 0/O/1/I)", fmt_ok, key_sample)

    # --- account_id derivado igual que el contrato ---
    import hashlib
    expected_acc = hashlib.sha256(key_sample.strip().encode()).hexdigest()[:16]
    check("account_id_for coincide con la definicion del contrato",
          licensing.account_id_for(key_sample) == expected_acc)

    # --- crear + validar (ok) ---
    created = licensing.create_license(plan="basic", days=30, daily_limit=20, notes="test")
    key = created["key"]
    res_ok = licensing.validate_key(key, machine_id="PC-1")
    check("validate de licencia valida -> valid True / reason ok",
          res_ok["valid"] is True and res_ok["reason"] == "ok", res_ok["reason"])
    check("validate devuelve account_id correcto",
          res_ok["account_id"] == licensing.account_id_for(key))
    check("validate devuelve daily_limit del plan", res_ok["daily_limit"] == 20,
          str(res_ok["daily_limit"]))

    # --- la clave NO se guarda en claro ---
    with sqlite3.connect(str(licensing.DB_PATH)) as conn:
        raw = conn.execute("SELECT key_hash FROM licenses").fetchall()
    stored = [r[0] for r in raw]
    check("en BD solo hay hashes (la clave en claro no aparece)",
          all(key not in s for s in stored))

    # --- inexistente ---
    res_nf = licensing.validate_key("ELEKA-MKT-ZZZZ-ZZZZ-ZZZZ")
    check("validate de clave inexistente -> not_found",
          res_nf["valid"] is False and res_nf["reason"] == "not_found", res_nf["reason"])

    # --- revocada ---
    rev_created = licensing.create_license(plan="basic", days=30)
    rev_key = rev_created["key"]
    licensing.revoke_license(rev_key)
    res_rev = licensing.validate_key(rev_key)
    check("validate de licencia revocada -> revoked",
          res_rev["valid"] is False and res_rev["reason"] == "revoked", res_rev["reason"])

    # --- expirada ---
    exp_key = _insert_expired_license()
    res_exp = licensing.validate_key(exp_key)
    check("validate de licencia expirada -> expired",
          res_exp["valid"] is False and res_exp["reason"] == "expired", res_exp["reason"])

    # --- binding machine_id: mismatch ---
    # 'key' ya quedo fijado a PC-1 arriba; validar con otra PC debe fallar.
    res_mm = licensing.validate_key(key, machine_id="PC-2")
    check("binding machine_id distinto -> machine_mismatch",
          res_mm["valid"] is False and res_mm["reason"] == "machine_mismatch", res_mm["reason"])
    # y la misma PC sigue funcionando
    res_same = licensing.validate_key(key, machine_id="PC-1")
    check("binding machine_id mismo -> sigue valido",
          res_same["valid"] is True and res_same["reason"] == "ok", res_same["reason"])

    # --- status no toca machine_id ---
    fresh = licensing.create_license(plan="basic", days=30)
    licensing.status_key(fresh["key"])  # consulta sin machine_id
    with sqlite3.connect(str(licensing.DB_PATH)) as conn:
        mid = conn.execute(
            "SELECT machine_id FROM licenses WHERE key_hash=?",
            (licensing._key_hash(fresh["key"]),),
        ).fetchone()[0]
    check("status no fija machine_id (sigue NULL)", mid is None)

    # --- list no expone claves en claro ---
    listed = licensing.list_licenses()
    all_keys = [key, rev_key, exp_key, fresh["key"]]
    leak = any(k in str(item) for item in listed for k in all_keys)
    check("list no expone ninguna clave en claro", not leak)

    # --- resumen ---
    total = len(_RESULTS)
    passed = sum(1 for r in _RESULTS if r)
    print(f"\nResultado: {passed}/{total} casos PASS")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run())
