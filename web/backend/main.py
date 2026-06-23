"""
Marketplace Automation - Web Backend (FastAPI + WebSocket)
==========================================================
Apartado web del proyecto. Reutiliza los modulos de /src:
  - PDFImageExtractor  -> extrae imagenes del PDF
  - AIImageAnalyzer    -> Gemini genera titulo/precio/descripcion/tags (JSON)
  - FacebookAuthenticator + MarketplaceAutomation -> publica con Selenium
  - ListingHistory     -> historial + logs + limite diario

Mismo enfoque que proxy-checker-pro y lk-vision: backend FastAPI que sirve el
frontend compilado en / y transmite el progreso por WebSocket.

IMPORTANTE: automatizar Facebook puede violar sus Terminos. Usar solo con
cuenta y productos propios, bajo tu responsabilidad.
"""
import os
import io
import sys
import json
import uuid
import queue
import asyncio
import datetime
import threading
from pathlib import Path
from typing import List
from collections import defaultdict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# --- importar modulos del repo (raiz/src) ---
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from config.settings import Config                       # noqa: E402
from modules.pdf_extractor import PDFImageExtractor      # noqa: E402
from modules.ai_analyzer import AIImageAnalyzer          # noqa: E402
from modules.facebook_auth import FacebookAuthenticator  # noqa: E402
from modules.marketplace_automation import MarketplaceAutomation  # noqa: E402
from modules.history import ListingHistory               # noqa: E402
from modules.human import human_gap                      # noqa: E402

app = FastAPI(title="Marketplace Automation - Web", version="1.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

# --- rutas de trabajo (relativas a web/backend) ---
WORK = Path(__file__).resolve().parent
TEMP_DIR = WORK / "temp_images"
TEMP_DIR.mkdir(exist_ok=True)
(WORK / "screenshots").mkdir(exist_ok=True)

cfg = Config()
# Modo demo: para el showcase publico (no abre Chrome ni publica de verdad)
DEMO_MODE = os.getenv("MARKETPLACE_DEMO", "0") == "1"
extractor = PDFImageExtractor(temp_dir=str(TEMP_DIR))
history = ListingHistory(str(WORK / "listings_history.json"), str(WORK / "logs"))
analyzer = None
if cfg.GEMINI_API_KEY:
    try:
        analyzer = AIImageAnalyzer(cfg.GEMINI_API_KEY, cfg.AI_MODEL_IMAGE, cfg.MAX_IMAGE_SIZE)
    except Exception as e:
        print(f"[IA] No se pudo iniciar: {e}")

# --- estado de sesion del navegador (herramienta de un solo usuario) ---
SESSION = {
    "auth": None,
    "driver": None,
    "marketplace": None,
    "logged_in": False,
    "logging_in": False,
    "needs_2fa": False,
}
_2fa_event = threading.Event()
_ai_cache_file = WORK / "ai_analysis_cache.json"


def _load_cache():
    if _ai_cache_file.exists():
        try:
            return json.loads(_ai_cache_file.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_cache(cache):
    _ai_cache_file.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


AI_CACHE = _load_cache()

# --- guard de uso para /api/analyze (protege la cuota gratuita de Gemini) ---
# El endpoint es publico (demo sin auth); limitamos analisis reales por dia.
ANALYZE_DAILY_GLOBAL = int(os.getenv("ANALYZE_DAILY_GLOBAL", "200"))
ANALYZE_DAILY_PER_IP = int(os.getenv("ANALYZE_DAILY_PER_IP", "30"))
_rate = {"date": None, "global": 0, "by_ip": defaultdict(int)}


def _rate_reset_if_needed():
    today = datetime.date.today().isoformat()
    if _rate["date"] != today:
        _rate["date"] = today
        _rate["global"] = 0
        _rate["by_ip"] = defaultdict(int)


def _rate_check(ip):
    _rate_reset_if_needed()
    if _rate["global"] >= ANALYZE_DAILY_GLOBAL:
        return False, "Limite diario global de analisis IA alcanzado. Intenta de nuevo manana."
    if _rate["by_ip"][ip] >= ANALYZE_DAILY_PER_IP:
        return False, f"Alcanzaste el limite de {ANALYZE_DAILY_PER_IP} analisis IA por dia para esta sesion."
    return True, None


def _rate_bump(ip):
    _rate["global"] += 1
    _rate["by_ip"][ip] += 1


# ======================================================================
#  Salud / configuracion
# ======================================================================
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "demo": DEMO_MODE,
        "ai_ready": analyzer is not None or DEMO_MODE,
        "ai_real": analyzer is not None,   # IA de verdad (no datos simulados)
        "logged_in": SESSION["logged_in"],
    }


# Datos simulados para el modo demo
_DEMO_PRODUCTS = [
    {"title": "Audifonos Bluetooth TWS Pro", "price": "17",
     "description": "GENTE LLEGARON LOS AUDIFONOS BLUETOOTH AL MEJOR PRECIO <3\n\n:) 1 unidad x 25 soles\n:D 3 unidades a mas x 17 soles (51 soles)\n\nSOMOS LK <3",
     "tags": ["audifonos", "bluetooth", "tws", "inalambrico", "musica", "gaming", "manos libres", "tecnologia"]},
    {"title": "Set de Ollas Antiadherentes 8pz", "price": "9",
     "description": "GENTE LLEGARON LAS OLLAS AL MEJOR PRECIO <3\n\n:) 1 unidad x 14 soles\n:D 3 unidades a mas x 9 soles (27 soles)\n\nSOMOS LK <3",
     "tags": ["ollas", "cocina", "antiadherente", "hogar", "set", "menaje", "utensilios", "calidad"]},
    {"title": "Mochila Escolar Impermeable", "price": "12",
     "description": "GENTE LLEGARON LAS MOCHILAS AL MEJOR PRECIO <3\n\n:) 1 unidad x 20 soles\n:D 3 unidades a mas x 12 soles (36 soles)\n\nSOMOS LK <3",
     "tags": ["mochila", "escolar", "impermeable", "viaje", "estudiantes", "resistente", "espaciosa", "moda"]},
]


def _demo_info(filename):
    idx = abs(hash(filename)) % len(_DEMO_PRODUCTS)
    return dict(_DEMO_PRODUCTS[idx])


@app.get("/api/config")
def get_config():
    return {
        "default_category": cfg.DEFAULT_CATEGORY,
        "default_condition": cfg.DEFAULT_CONDITION,
        "human_min_delay": cfg.HUMAN_MIN_DELAY,
        "human_max_delay": cfg.HUMAN_MAX_DELAY,
        "listing_min_gap": cfg.LISTING_MIN_GAP,
        "listing_max_gap": cfg.LISTING_MAX_GAP,
        "max_listings_per_day": cfg.MAX_LISTINGS_PER_DAY,
        "max_retries": cfg.MAX_RETRIES,
        "remaining_today": history.remaining_today(cfg.MAX_LISTINGS_PER_DAY),
    }


@app.post("/api/config")
async def set_config(payload: dict):
    for key, attr in {
        "default_category": "DEFAULT_CATEGORY",
        "default_condition": "DEFAULT_CONDITION",
        "human_min_delay": "HUMAN_MIN_DELAY",
        "human_max_delay": "HUMAN_MAX_DELAY",
        "listing_min_gap": "LISTING_MIN_GAP",
        "listing_max_gap": "LISTING_MAX_GAP",
        "max_listings_per_day": "MAX_LISTINGS_PER_DAY",
        "max_retries": "MAX_RETRIES",
    }.items():
        if key in payload and payload[key] is not None:
            setattr(cfg, attr, payload[key])
    return get_config()


# ======================================================================
#  PDF -> imagenes
# ======================================================================
@app.post("/api/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Sube un archivo PDF")
    # limpiar imagenes anteriores
    extractor.cleanup()
    dest = WORK / "upload.pdf"
    dest.write_bytes(await file.read())
    try:
        paths = extractor.extract_images_from_pdf(str(dest))
    except Exception as e:
        raise HTTPException(500, f"No se pudo procesar el PDF: {e}")
    items = []
    for i, p in enumerate(paths, 1):
        fn = os.path.basename(p)
        items.append({"page": i, "filename": fn, "url": f"/api/img/{fn}"})
    return {"count": len(items), "items": items}


@app.post("/api/upload-images")
async def upload_images(files: List[UploadFile] = File(...)):
    """Sube fotos directamente (sin PDF): seleccion multiple, pegado o arrastrar.
    Cada imagen se normaliza a PNG y se agrega al set de trabajo."""
    saved = []
    for f in files:
        ct = (f.content_type or "").lower()
        if not ct.startswith("image/"):
            continue
        try:
            data = await f.read()
            img = Image.open(io.BytesIO(data)).convert("RGB")
        except Exception:
            continue
        fn = f"img_{uuid.uuid4().hex[:10]}.png"
        img.save(TEMP_DIR / fn, "PNG")
        saved.append({"filename": fn, "url": f"/api/img/{fn}"})
    if not saved:
        raise HTTPException(400, "No se recibieron imagenes validas (sube JPG/PNG)")
    return {"count": len(saved), "items": saved}


@app.get("/api/img/{filename}")
def get_image(filename: str):
    safe = os.path.basename(filename)
    fp = TEMP_DIR / safe
    if not fp.exists():
        raise HTTPException(404, "imagen no encontrada")
    return FileResponse(fp)


# ======================================================================
#  Analisis IA
# ======================================================================
@app.post("/api/analyze")
async def analyze(payload: dict, request: Request):
    fn = os.path.basename(payload.get("filename", ""))
    # ---- IA REAL: si hay analyzer (GEMINI_API_KEY presente) se analiza de verdad,
    #      aunque el resto de la demo (publicacion) siga simulado. ----
    if analyzer:
        fp = TEMP_DIR / fn
        if not fp.exists():
            raise HTTPException(404, "imagen no encontrada")
        if fn in AI_CACHE and not payload.get("force"):
            return {"cached": True, "real": True, **AI_CACHE[fn]}
        ip = request.client.host if request.client else "?"
        ok, msg = _rate_check(ip)
        if not ok:
            raise HTTPException(429, msg)
        info = await asyncio.to_thread(analyzer.analyze_image_for_marketplace, str(fp))
        _rate_bump(ip)
        AI_CACHE[fn] = info
        _save_cache(AI_CACHE)
        return {"cached": False, "real": True, **info}
    # ---- Fallback simulado (sin key) ----
    if DEMO_MODE:
        await asyncio.sleep(0.8)  # simular el tiempo de la IA
        info = _demo_info(fn)
        AI_CACHE[fn] = info
        return {"cached": False, "demo": True, **info}
    raise HTTPException(400, "Falta GEMINI_API_KEY en el .env")


# ======================================================================
#  Login / sesion
# ======================================================================
def _do_login():
    SESSION["logging_in"] = True
    SESSION["needs_2fa"] = False
    _2fa_event.clear()

    def twofa_cb():
        SESSION["needs_2fa"] = True
        _2fa_event.wait(timeout=300)  # espera a /api/2fa-confirm
        SESSION["needs_2fa"] = False
        return _2fa_event.is_set()

    try:
        auth = FacebookAuthenticator(
            email=cfg.FACEBOOK_EMAIL, password=cfg.FACEBOOK_PASSWORD,
            two_fa_secret=cfg.FACEBOOK_2FA_SECRET, headless=cfg.HEADLESS,
            implicit_wait=cfg.IMPLICIT_WAIT, twofa_callback=twofa_cb,
            user_data_dir=cfg.USER_DATA_DIR,
        )
        driver = auth.login()
        if driver:
            SESSION.update({
                "auth": auth, "driver": driver,
                "marketplace": MarketplaceAutomation(driver, cfg.HUMAN_MIN_DELAY, cfg.HUMAN_MAX_DELAY),
                "logged_in": True,
            })
        else:
            SESSION["logged_in"] = False
    except Exception as e:
        print(f"[LOGIN] error: {e}")
        SESSION["logged_in"] = False
    finally:
        SESSION["logging_in"] = False


@app.post("/api/login")
async def login():
    if DEMO_MODE:
        SESSION["logged_in"] = True
        return {"status": "demo_conectado"}
    if SESSION["logged_in"]:
        return {"status": "ya_conectado"}
    if SESSION["logging_in"]:
        return {"status": "en_progreso", "needs_2fa": SESSION["needs_2fa"]}
    if not cfg.FACEBOOK_EMAIL or not cfg.FACEBOOK_PASSWORD:
        raise HTTPException(400, "Faltan credenciales de Facebook en el .env")
    threading.Thread(target=_do_login, daemon=True).start()
    return {"status": "iniciando"}


@app.get("/api/session")
def session_status():
    return {
        "logged_in": SESSION["logged_in"],
        "logging_in": SESSION["logging_in"],
        "needs_2fa": SESSION["needs_2fa"],
    }


@app.post("/api/2fa-confirm")
def confirm_2fa():
    _2fa_event.set()
    return {"ok": True}


# ======================================================================
#  Historial
# ======================================================================
@app.get("/api/history")
def get_history():
    return {"summary": history.summary(), "records": history._records[-200:][::-1]}


# ======================================================================
#  Publicacion en vivo (WebSocket)
# ======================================================================
def _publish_worker(items, evq: "queue.Queue"):
    """Corre en un thread; empuja eventos de progreso a la cola."""
    import time as _t
    def emit(**ev):
        evq.put(ev)

    # ---- MODO DEMO: simula la publicacion sin Selenium ni Facebook ----
    if DEMO_MODE:
        total = len(items)
        emit(type="start", total=total, remaining_today=cfg.MAX_LISTINGS_PER_DAY)
        ok = 0
        for i, item in enumerate(items, 1):
            fn = os.path.basename(item.get("filename", f"item{i}"))
            info = {"title": item.get("title") or _demo_info(fn)["title"], "price": item.get("price") or "15"}
            emit(type="item_start", page=i, filename=fn)
            emit(type="log", message=f"[DEMO] Analizando {fn}...")
            _t.sleep(0.6)
            emit(type="log", message=f"[DEMO] Publicando '{info['title']}'...")
            _t.sleep(1.0)
            ok += 1
            history.record(fn, info["title"], str(info["price"]), "success", attempts=1)
            emit(type="item_done", page=i, status="success", title=info["title"], price=info["price"])
            emit(type="progress", done=i, total=total, ok=ok, fail=0)
            if i < total:
                emit(type="waiting", seconds=2)
                _t.sleep(2)
        emit(type="done", ok=ok, fail=0, total=total)
        evq.put(None)
        return

    if not SESSION["logged_in"] or not SESSION["marketplace"]:
        emit(type="error", message="No hay sesion de Facebook. Inicia sesion primero.")
        evq.put(None)
        return
    if not analyzer:
        emit(type="error", message="Falta GEMINI_API_KEY.")
        evq.put(None)
        return

    market = SESSION["marketplace"]
    remaining = history.remaining_today(cfg.MAX_LISTINGS_PER_DAY)
    if remaining <= 0:
        emit(type="error", message=f"Limite diario de {cfg.MAX_LISTINGS_PER_DAY} alcanzado.")
        evq.put(None)
        return

    total = len(items)
    ok = fail = 0
    emit(type="start", total=total, remaining_today=remaining)

    for i, item in enumerate(items, 1):
        if ok >= remaining:
            emit(type="log", message="Limite diario alcanzado, deteniendo.")
            break
        fn = os.path.basename(item.get("filename", ""))
        fp = TEMP_DIR / fn
        emit(type="item_start", page=i, filename=fn)

        # info: usa override del usuario o cache o IA
        info = None
        if item.get("title") and item.get("price") and item.get("description"):
            info = {"title": item["title"], "price": str(item["price"]),
                    "description": item["description"], "tags": item.get("tags", [])}
        elif fn in AI_CACHE:
            info = AI_CACHE[fn]
        else:
            try:
                emit(type="log", message=f"Analizando {fn} con IA...")
                info = analyzer.analyze_image_for_marketplace(str(fp))
                AI_CACHE[fn] = info
                _save_cache(AI_CACHE)
            except Exception as e:
                fail += 1
                history.record(fn, "(analisis fallido)", "0", "failed", error=e)
                emit(type="item_done", page=i, status="failed", error=str(e))
                continue

        # publicar con reintentos
        success = False
        attempts = 0
        for attempt in range(1, cfg.MAX_RETRIES + 2):
            attempts = attempt
            emit(type="log", message=f"Publicando '{info['title']}' (intento {attempt})...")
            try:
                success = market.create_listing(
                    title=info["title"], price=info["price"], description=info["description"],
                    category=cfg.DEFAULT_CATEGORY, condition=cfg.DEFAULT_CONDITION,
                    images=[str(fp)], tags=info.get("tags", []),
                )
            except Exception as e:
                emit(type="log", message=f"Error: {e}")
                success = False
            if success:
                break

        if success:
            ok += 1
            history.record(fn, info["title"], info["price"], "success", attempts=attempts)
            emit(type="item_done", page=i, status="success", title=info["title"], price=info["price"])
        else:
            fail += 1
            history.record(fn, info["title"], info["price"], "failed", attempts=attempts, error="create_listing False")
            emit(type="item_done", page=i, status="failed", title=info["title"])

        emit(type="progress", done=i, total=total, ok=ok, fail=fail)

        # pausa humana entre publicaciones
        if i < total and ok < remaining:
            gap = int((cfg.LISTING_MIN_GAP + cfg.LISTING_MAX_GAP) / 2)
            emit(type="waiting", seconds=gap)
            human_gap(cfg.LISTING_MIN_GAP, cfg.LISTING_MAX_GAP)

    emit(type="done", ok=ok, fail=fail, total=total)
    evq.put(None)


@app.websocket("/api/ws/publish")
async def ws_publish(ws: WebSocket):
    await ws.accept()
    try:
        payload = await ws.receive_json()
        items = payload.get("items", [])
        if not items:
            await ws.send_json({"type": "error", "message": "No hay productos seleccionados"})
            await ws.close()
            return

        evq: "queue.Queue" = queue.Queue()
        threading.Thread(target=_publish_worker, args=(items, evq), daemon=True).start()

        loop = asyncio.get_event_loop()
        while True:
            ev = await loop.run_in_executor(None, evq.get)
            if ev is None:
                break
            await ws.send_json(ev)
        await ws.close()
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await ws.send_json({"type": "error", "message": str(e)})
            await ws.close()
        except Exception:
            pass


# ======================================================================
#  Frontend compilado (React build) servido en /
# ======================================================================
DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(DIST / "assets")), name="assets")

    @app.get("/")
    def index():
        return FileResponse(DIST / "index.html")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        # Evita path traversal: la ruta resuelta debe quedar dentro de DIST.
        dist_root = DIST.resolve()
        fp = (dist_root / full_path).resolve()
        if fp.is_file() and dist_root in fp.parents:
            return FileResponse(fp)
        return FileResponse(dist_root / "index.html")
else:
    @app.get("/")
    def no_build():
        return {"msg": "Frontend no compilado. Corre: cd web/frontend && npm install && npm run build"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8300, reload=False)
