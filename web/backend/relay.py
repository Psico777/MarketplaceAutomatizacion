"""
ELEKA Marketplace - Relay + cola de jobs (cloud)
================================================
Componente DUEÑO: Agente 2 (ver docs/HYBRID_CONTRACT.md, seccion 3).

Hace de puente entre el dashboard web (navegador) y el agente local (.exe en la
PC del cliente). El agente abre una conexion WebSocket SALIENTE hacia el cloud;
el relay le despacha los jobs publicados desde el dashboard y reenvia de vuelta
los eventos de progreso a los suscriptores del dashboard.

Self-contained: este modulo NO toca main.py. Solo importa de `licensing` las dos
funciones del contrato (`validate_key`, `account_id_for`). Se expone como un
`APIRouter` en la variable `router`, que el orquestador incluira en main.py.

La publicacion real a Facebook NUNCA corre aqui; solo en el agente local.
"""
import os
import json
import asyncio
import hashlib
from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse

# ----------------------------------------------------------------------
#  Import de la API de licencias (la construye Agente 1 en licensing.py).
#  Como puede que aun no exista cuando se trabaja en paralelo, hacemos el
#  import robusto: si falla, usamos un stub local equivalente.
#
#  Stub:
#   - account_id_for: identico al contrato (sha256[:16]).
#   - validate_key  : SOLO para poder autotestear sin el modulo real. Acepta
#                     cualquier clave NO vacia UNICAMENTE si la variable de
#                     entorno RELAY_ALLOW_INSECURE == "1". En cualquier otro
#                     caso rechaza (no se permite operar sin licencias reales).
# ----------------------------------------------------------------------
try:
    from licensing import validate_key, account_id_for  # type: ignore
    _LICENSING_REAL = True
except Exception:  # ImportError u otro fallo de carga del modulo real
    _LICENSING_REAL = False

    def account_id_for(key: str) -> str:
        # Misma derivacion que el contrato (seccion 0).
        return hashlib.sha256(key.strip().encode()).hexdigest()[:16]

    def validate_key(key: str, machine_id: str | None = None) -> dict:
        # Stub inseguro deliberado: solo para autotest local.
        insecure = os.getenv("RELAY_ALLOW_INSECURE") == "1"
        if insecure and key and key.strip():
            return {
                "valid": True,
                "account_id": account_id_for(key),
                "plan": "insecure-test",
                "expires_at": None,
                "daily_limit": 20,
                "reason": "ok",
            }
        return {
            "valid": False,
            "account_id": account_id_for(key) if key else "",
            "plan": None,
            "expires_at": None,
            "daily_limit": 0,
            "reason": "no_licensing_module",
        }


# ----------------------------------------------------------------------
#  Rutas de trabajo. Las imagenes que el dashboard subio via /api/upload-images
#  viven en web/backend/temp_images/<filename> (mismo directorio que usa main.py).
# ----------------------------------------------------------------------
WORK = Path(__file__).resolve().parent
TEMP_DIR = WORK / "temp_images"
TEMP_DIR.mkdir(exist_ok=True)

router = APIRouter()

# ----------------------------------------------------------------------
#  Estado en memoria (seccion 3 del contrato).
#   AGENTS : account_id -> WebSocket del agente conectado.
#   JOBS   : job_id     -> dict del job (account_id, items, settings, status...).
#   SUBS   : job_id     -> lista de WebSocket de dashboards suscritos al job.
#   QUEUE  : account_id -> lista de job_id pendientes (agente offline).
# ----------------------------------------------------------------------
AGENTS: Dict[str, WebSocket] = {}
JOBS: Dict[str, dict] = {}
SUBS: Dict[str, List[WebSocket]] = {}
QUEUE: Dict[str, List[str]] = {}

# Tipos de evento del agente que se reenvian tal cual a los suscriptores.
_FORWARD_TYPES = {"progress", "item_done", "job_done", "status", "job_accepted"}


def _new_job_id() -> str:
    # Identificador corto y legible, consistente con el ejemplo del contrato (j_ab12...).
    return "j_" + hashlib.sha256(os.urandom(16)).hexdigest()[:8]


def _build_publish_message(job: dict) -> dict:
    """Construye el mensaje publish_job para el agente, convirtiendo los
    nombres de archivo (image_files) en URLs absolutas servidas por el relay
    (/api/jobs/<job_id>/img/<idx>), tal como exige el contrato."""
    job_id = job["job_id"]
    items_out = []
    for item in job["items"]:
        files = item.get("image_files") or []
        image_urls = [f"/api/jobs/{job_id}/img/{idx}" for idx in range(len(files))]
        items_out.append({
            "page": item.get("page"),
            "title": item.get("title"),
            "price": item.get("price"),
            "description": item.get("description"),
            "tags": item.get("tags", []),
            "image_urls": image_urls,
        })
    return {
        "type": "publish_job",
        "job_id": job_id,
        "items": items_out,
        "settings": job.get("settings", {}),
    }


async def _dispatch_job(job: dict) -> bool:
    """Envia el job al agente de su cuenta si esta online. Devuelve True si se
    despacho, False si no hay agente conectado."""
    ws = AGENTS.get(job["account_id"])
    if ws is None:
        return False
    try:
        await ws.send_json(_build_publish_message(job))
        job["status"] = "dispatched"
        return True
    except Exception:
        # El agente murio entre medias: lo damos por desconectado.
        AGENTS.pop(job["account_id"], None)
        return False


async def _forward_to_subs(job_id: str, message: dict) -> None:
    """Reenvia un evento a todos los dashboards suscritos al job. Limpia los
    sockets que ya esten cerrados."""
    subs = SUBS.get(job_id, [])
    dead = []
    for sub in subs:
        try:
            await sub.send_json(message)
        except Exception:
            dead.append(sub)
    for d in dead:
        if d in subs:
            subs.remove(d)


# ======================================================================
#  WebSocket del AGENTE (conexion saliente desde la PC del cliente)
# ======================================================================
@router.websocket("/api/agent/ws")
async def agent_ws(ws: WebSocket):
    """Conexion del agente local. Valida licencia, registra el agente, despacha
    los jobs encolados y reenvia los eventos del agente al dashboard."""
    # Los parametros viajan en el query string (key, machine_id).
    key = ws.query_params.get("key", "")
    machine_id = ws.query_params.get("machine_id")

    info = validate_key(key, machine_id)
    if not info.get("valid"):
        # Aceptar para poder cerrar con un code/reason claro (4001 = licencia invalida).
        await ws.accept()
        await ws.close(code=4001, reason=info.get("reason", "invalid_license"))
        return

    account_id = info["account_id"]
    await ws.accept()

    # Si habia otro agente registrado para esta cuenta, lo reemplazamos.
    old = AGENTS.get(account_id)
    if old is not None and old is not ws:
        try:
            await old.close(code=4002, reason="replaced_by_new_agent")
        except Exception:
            pass
    AGENTS[account_id] = ws

    # Despachar jobs que quedaron encolados mientras el agente estaba offline.
    pending = QUEUE.pop(account_id, [])
    for job_id in pending:
        job = JOBS.get(job_id)
        if job and job.get("status") == "queued":
            await _dispatch_job(job)

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except Exception:
                continue
            mtype = msg.get("type")

            if mtype == "ping":
                await ws.send_json({"type": "pong"})
                continue
            if mtype == "pong":
                # Respuesta a un ping nuestro: nada que hacer.
                continue
            if mtype == "hello":
                # Handshake inicial del agente; lo registramos en el estado del agente.
                continue

            # Eventos de progreso del job -> reenviar a los dashboards suscritos.
            if mtype in _FORWARD_TYPES:
                job_id = msg.get("job_id")
                if mtype == "job_done" and job_id in JOBS:
                    JOBS[job_id]["status"] = "done"
                if job_id:
                    await _forward_to_subs(job_id, msg)
                continue
            # Cualquier otro tipo se ignora silenciosamente (forward-compat).
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        # Desregistrar solo si seguimos siendo el agente activo de la cuenta.
        if AGENTS.get(account_id) is ws:
            AGENTS.pop(account_id, None)


# ======================================================================
#  Lado DASHBOARD
# ======================================================================
@router.post("/api/jobs/publish")
async def publish_job(payload: dict):
    """Publica un job desde el dashboard. Si el agente de la cuenta esta online
    se despacha al momento (dispatched); si no, queda encolado (queued)."""
    account_id = payload.get("account_id")
    items = payload.get("items")
    if not account_id:
        raise HTTPException(400, "Falta account_id")
    if not items:
        raise HTTPException(400, "El job no tiene items")

    job_id = _new_job_id()
    job = {
        "job_id": job_id,
        "account_id": account_id,
        "items": items,
        "settings": payload.get("settings", {}),
        "status": "queued",
    }
    JOBS[job_id] = job

    dispatched = await _dispatch_job(job)
    if dispatched:
        return {"job_id": job_id, "status": "dispatched"}

    # Agente offline: encolar para entregarlo cuando se conecte.
    QUEUE.setdefault(account_id, []).append(job_id)
    job["status"] = "queued"
    return {"job_id": job_id, "status": "queued"}


@router.websocket("/api/jobs/ws/{job_id}")
async def job_ws(ws: WebSocket, job_id: str):
    """Suscripcion del dashboard a los eventos de progreso de un job."""
    await ws.accept()
    SUBS.setdefault(job_id, []).append(ws)

    # Informar al dashboard del estado actual del job al suscribirse.
    job = JOBS.get(job_id)
    if job is None:
        await ws.send_json({"type": "error", "message": "job no encontrado"})
    else:
        await ws.send_json({"type": "subscribed", "job_id": job_id, "status": job["status"]})

    try:
        # El dashboard solo escucha; mantenemos el socket abierto leyendo.
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        subs = SUBS.get(job_id, [])
        if ws in subs:
            subs.remove(ws)
        if not subs:
            SUBS.pop(job_id, None)


@router.get("/api/agent/online")
async def agent_online(account_id: str):
    """Indica si el agente de una cuenta esta conectado en este momento."""
    return {"online": account_id in AGENTS}


@router.get("/api/jobs/{job_id}/img/{idx}")
async def job_image(job_id: str, idx: int):
    """Sirve los bytes de la imagen image_files[idx] del job desde temp_images/.
    Lo usa el agente para descargar las fotos antes de publicar."""
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(404, "job no encontrado")
    items = job.get("items", [])
    # Buscamos el item que contenga el indice global solicitado. El contrato
    # numera image_urls por item, asi que aceptamos tanto numeracion por item
    # como un indice plano dentro del primer item que aplique.
    # Implementacion: para cada item, sus image_files se exponen como 0..n-1.
    for item in items:
        files = item.get("image_files") or []
        if 0 <= idx < len(files):
            safe = os.path.basename(files[idx])
            fp = TEMP_DIR / safe
            if not fp.exists():
                raise HTTPException(404, "imagen no encontrada")
            return FileResponse(fp)
    raise HTTPException(404, "indice de imagen fuera de rango")
