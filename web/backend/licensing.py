"""
ELEKA Marketplace - API de licencias (cloud)
============================================
Router FastAPI self-contained (prefijo /api/license). No importa nada de main.py.
Persistencia con sqlite3 (stdlib) en web/backend/licenses.db.

Funciones importables por el relay:
  - validate_key(key, machine_id=None) -> dict   (mismo dict que /validate)
  - account_id_for(key) -> str

Reglas del contrato (docs/HYBRID_CONTRACT.md, secciones 0, 1 y 2):
  - Clave: ELEKA-MKT-XXXX-XXXX-XXXX (mayusculas, sin caracteres ambiguos 0/O/1/I).
  - En la BD se guarda SOLO sha256(key); nunca la clave en claro.
  - account_id = sha256(key)[:16].
  - machine_id: NULL hasta el primer validate; luego queda fijado (1 licencia = 1 PC).
  - Token admin desde la variable de entorno ELEKA_ADMIN_TOKEN.

IMPORTANTE: sin secretos hardcodeados.
"""
import os
import secrets
import sqlite3
import hashlib
import datetime
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

# --- rutas / constantes ---
DB_PATH = Path(__file__).resolve().parent / "licenses.db"

# Alfabeto sin caracteres ambiguos (sin 0/O/1/I) para los grupos de la clave.
KEY_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
KEY_PREFIX = "ELEKA-MKT"
KEY_GROUPS = 3          # 3 grupos despues del prefijo: XXXX-XXXX-XXXX
KEY_GROUP_LEN = 4

DEFAULT_DAILY_LIMIT = 20
VALID_REASONS = {"ok", "not_found", "revoked", "expired", "machine_mismatch"}


# ======================================================================
#  Capa de datos (SIN dependencia de FastAPI)
# ======================================================================
def account_id_for(key: str) -> str:
    """Deriva el id de cuenta a partir de la clave (igual que el relay).

    Definicion compartida en el contrato (seccion 0)."""
    return hashlib.sha256(key.strip().encode()).hexdigest()[:16]


def _key_hash(key: str) -> str:
    """sha256 de la clave normalizada (lo unico que se guarda en BD)."""
    return hashlib.sha256(key.strip().encode()).hexdigest()


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _iso(dt: datetime.datetime) -> str:
    return dt.isoformat()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Crea la tabla licenses si no existe (esquema exacto del contrato)."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS licenses (
                key_hash    TEXT PRIMARY KEY,
                account_id  TEXT,
                plan        TEXT,
                status      TEXT,
                machine_id  TEXT,
                created_at  TEXT,
                expires_at  TEXT,
                daily_limit INTEGER,
                notes       TEXT
            )
            """
        )
        conn.commit()


def generate_key() -> str:
    """Genera una clave ELEKA-MKT-XXXX-XXXX-XXXX (mayusculas, sin 0/O/1/I)."""
    groups = [
        "".join(secrets.choice(KEY_ALPHABET) for _ in range(KEY_GROUP_LEN))
        for _ in range(KEY_GROUPS)
    ]
    return "-".join([KEY_PREFIX, *groups])


def create_license(plan: str = "basic", days: int = 30,
                   daily_limit: int = DEFAULT_DAILY_LIMIT, notes: str = "") -> dict:
    """Crea una licencia y devuelve la clave EN CLARO (solo aqui, una vez).

    Reintenta si por azar la clave colisiona con una existente."""
    init_db()
    created = _now()
    expires = created + datetime.timedelta(days=int(days)) if days and int(days) > 0 else None
    expires_iso = _iso(expires) if expires else None

    with _connect() as conn:
        for _ in range(10):
            key = generate_key()
            kh = _key_hash(key)
            try:
                conn.execute(
                    """
                    INSERT INTO licenses
                        (key_hash, account_id, plan, status, machine_id,
                         created_at, expires_at, daily_limit, notes)
                    VALUES (?, ?, ?, 'active', NULL, ?, ?, ?, ?)
                    """,
                    (kh, account_id_for(key), plan, _iso(created),
                     expires_iso, int(daily_limit), notes or ""),
                )
                conn.commit()
                return {
                    "key": key,
                    "account_id": account_id_for(key),
                    "expires_at": expires_iso,
                }
            except sqlite3.IntegrityError:
                continue  # colision improbable: reintentar con otra clave
    raise RuntimeError("No se pudo generar una clave unica tras varios intentos")


def revoke_license(key: str) -> bool:
    """Marca una licencia como revocada. Devuelve True si existia."""
    init_db()
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE licenses SET status='revoked' WHERE key_hash=?",
            (_key_hash(key),),
        )
        conn.commit()
        return cur.rowcount > 0


def list_licenses() -> list:
    """Lista licencias SIN exponer claves en claro (key_hash parcial)."""
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT key_hash, account_id, plan, status, expires_at, machine_id
            FROM licenses ORDER BY created_at DESC
            """
        ).fetchall()
    out = []
    for r in rows:
        out.append({
            "key_hash": (r["key_hash"][:12] + "..."),
            "account_id": r["account_id"],
            "plan": r["plan"],
            "status": r["status"],
            "expires_at": r["expires_at"],
            "machine_id": r["machine_id"],
        })
    return out


def _is_expired(expires_at: str | None, now: datetime.datetime) -> bool:
    if not expires_at:
        return False
    try:
        exp = datetime.datetime.fromisoformat(expires_at)
    except ValueError:
        return False
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=datetime.timezone.utc)
    return now >= exp


def _result(valid: bool, row, reason: str) -> dict:
    """Construye el dict de respuesta con el shape exacto del contrato."""
    return {
        "valid": valid,
        "account_id": row["account_id"] if row else account_id_for(""),
        "plan": row["plan"] if row else None,
        "expires_at": row["expires_at"] if row else None,
        "daily_limit": row["daily_limit"] if row else 0,
        "reason": reason,
    }


def validate_key(key: str, machine_id: str | None = None) -> dict:
    """Valida una clave y (si machine_id viene) la fija al primer uso.

    Devuelve el mismo dict que POST /api/license/validate. La usa el relay."""
    init_db()
    now = _now()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM licenses WHERE key_hash=?",
            (_key_hash(key),),
        ).fetchone()

        if row is None:
            return _result(False, None, "not_found")
        if row["status"] != "active":
            return _result(False, row, "revoked")
        if _is_expired(row["expires_at"], now):
            return _result(False, row, "expired")

        # Binding de machine_id: si ya esta fijado debe coincidir.
        bound = row["machine_id"]
        if bound:
            if machine_id is not None and machine_id != bound:
                return _result(False, row, "machine_mismatch")
        elif machine_id:
            # Primer validate con machine_id: lo fijamos (1 licencia = 1 PC).
            conn.execute(
                "UPDATE licenses SET machine_id=? WHERE key_hash=?",
                (machine_id, row["key_hash"]),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM licenses WHERE key_hash=?",
                (row["key_hash"],),
            ).fetchone()

        return _result(True, row, "ok")


def status_key(key: str) -> dict:
    """Como validate pero SIN tocar machine_id (consulta de estado)."""
    init_db()
    now = _now()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM licenses WHERE key_hash=?",
            (_key_hash(key),),
        ).fetchone()
    if row is None:
        return _result(False, None, "not_found")
    if row["status"] != "active":
        return _result(False, row, "revoked")
    if _is_expired(row["expires_at"], now):
        return _result(False, row, "expired")
    return _result(True, row, "ok")


# ======================================================================
#  Capa REST (FastAPI)
# ======================================================================
router = APIRouter(prefix="/api/license", tags=["license"])

# Inicializa la BD al importar el router.
init_db()


class ValidateBody(BaseModel):
    key: str
    machine_id: str | None = None


class CreateBody(BaseModel):
    plan: str = "basic"
    days: int = 30
    daily_limit: int = DEFAULT_DAILY_LIMIT
    notes: str = ""


class RevokeBody(BaseModel):
    key: str


def _require_admin(token: str | None) -> None:
    """Valida el token admin contra ELEKA_ADMIN_TOKEN. 401 si no coincide."""
    expected = os.getenv("ELEKA_ADMIN_TOKEN")
    if not expected or not token or not secrets.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Token de administrador invalido")


# --- REST publico ---
@router.post("/validate")
def validate(body: ValidateBody):
    return validate_key(body.key, body.machine_id)


@router.get("/status")
def status(x_license_key: str | None = Header(default=None)):
    if not x_license_key:
        raise HTTPException(status_code=400, detail="Falta el header X-License-Key")
    return status_key(x_license_key)


# --- Admin (requiere X-Admin-Token) ---
@router.post("/admin/create")
def admin_create(body: CreateBody, x_admin_token: str | None = Header(default=None)):
    _require_admin(x_admin_token)
    return create_license(body.plan, body.days, body.daily_limit, body.notes)


@router.get("/admin/list")
def admin_list(x_admin_token: str | None = Header(default=None)):
    _require_admin(x_admin_token)
    return list_licenses()


@router.post("/admin/revoke")
def admin_revoke(body: RevokeBody, x_admin_token: str | None = Header(default=None)):
    _require_admin(x_admin_token)
    ok = revoke_license(body.key)
    if not ok:
        raise HTTPException(status_code=404, detail="Licencia no encontrada")
    return {"ok": True}
