"""
ELEKA Marketplace - Agente local (.exe).

Corre en la PC del cliente. Abre una conexion WebSocket SALIENTE hacia el cloud
(eleka.me), recibe jobs de publicacion y los ejecuta con Selenium contra Facebook
Marketplace usando la cuenta y la IP del cliente.

Reutiliza el codigo existente del repo (no lo reimplementa):
  - modules.facebook_auth.FacebookAuthenticator  (login + 2FA + perfil persistente)
  - modules.marketplace_automation.MarketplaceAutomation  (create_listing)
  - modules.human  (delays humanos)

El protocolo (mensajes WebSocket, endpoints, identidad de cuenta) sigue al pie de
la letra docs/HYBRID_CONTRACT.md. Este modulo NO importa nada del backend web.

Flags:
  --simulate   ejecuta TODO el flujo del protocolo SIN abrir Chrome (eventos
               simulando exito). Esencial para autotestear el handshake/relay.
  --once       procesa un solo job y termina (util para tests).
  --cloud-url  sobrescribe la cloud_url de config (util para tests locales).
"""
import argparse
import asyncio
import hashlib
import json
import os
import sys
import tempfile
import time
import uuid
from pathlib import Path

import requests

try:
    import websockets
except ImportError:  # pragma: no cover - dependencia obligatoria en runtime
    print("Falta la dependencia 'websockets'. Instala con: pip install websockets")
    raise

AGENT_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
#  Rutas y reutilizacion de los modulos del repo
# ---------------------------------------------------------------------------
# Igual que web/backend/main.py: anadimos <repo>/src a sys.path.
# En desarrollo, agent.py vive en <repo>/agent/, asi que la raiz es parent.parent.
# Empaquetado con PyInstaller, los modulos se incluyen via --add-data y quedan en
# el directorio temporal sys._MEIPASS bajo "src".
def _repo_src_dirs():
    """Devuelve las rutas candidatas donde puede vivir 'src' (dev o empaquetado)."""
    candidates = []
    if getattr(sys, "frozen", False):
        # Ejecutable PyInstaller: los datos van en _MEIPASS.
        base = Path(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)))
        candidates.append(base / "src")
        candidates.append(base)
    here = Path(__file__).resolve().parent
    candidates.append(here.parent / "src")  # <repo>/src en desarrollo
    return candidates


for _src in _repo_src_dirs():
    if _src.exists():
        sys.path.insert(0, str(_src))
        break


# ---------------------------------------------------------------------------
#  Identidad de cuenta (igual que el contrato, seccion 0)
# ---------------------------------------------------------------------------
def account_id_for(key: str) -> str:
    return hashlib.sha256(key.strip().encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
#  Configuracion local
# ---------------------------------------------------------------------------
CONFIG_DIR = Path(os.path.expanduser("~")) / ".eleka-marketplace"
CONFIG_PATH = CONFIG_DIR / "config.json"
CHROME_PROFILE_DIR = CONFIG_DIR / "chrome-profile"
DEFAULT_CLOUD_URL = "https://market.eleka.me"


def load_config(cloud_url_override=None) -> dict:
    """Carga (o crea) la config local. Pide la clave por consola si falta."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cfg = {}
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            cfg = {}

    cfg.setdefault("cloud_url", DEFAULT_CLOUD_URL)
    # machine_id: uuid4 persistido (1 licencia = 1 PC).
    if not cfg.get("machine_id"):
        cfg["machine_id"] = str(uuid.uuid4())

    if cloud_url_override:
        cfg["cloud_url"] = cloud_url_override

    # license_key: si falta, pedirla por consola y guardarla.
    if not cfg.get("license_key"):
        try:
            key = input("Introduce tu clave de licencia (ELEKA-MKT-...): ").strip()
        except (EOFError, KeyboardInterrupt):
            key = ""
        if not key:
            print("No se proporciono clave de licencia. Saliendo.")
            sys.exit(1)
        cfg["license_key"] = key

    save_config(cfg)
    return cfg


def save_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
#  Validacion de licencia (REST)
# ---------------------------------------------------------------------------
def validate_license(cloud_url: str, key: str, machine_id: str) -> dict:
    """POST {cloud_url}/api/license/validate. Devuelve el dict de respuesta."""
    url = cloud_url.rstrip("/") + "/api/license/validate"
    resp = requests.post(url, json={"key": key, "machine_id": machine_id}, timeout=20)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
#  Utilidades de WebSocket URL
# ---------------------------------------------------------------------------
def build_ws_url(cloud_url: str, key: str, machine_id: str) -> str:
    """Convierte http(s)://host a ws(s)://host/api/agent/ws?key=...&machine_id=..."""
    from urllib.parse import quote
    base = cloud_url.rstrip("/")
    if base.startswith("https://"):
        ws_base = "wss://" + base[len("https://"):]
    elif base.startswith("http://"):
        ws_base = "ws://" + base[len("http://"):]
    else:
        ws_base = base
    return f"{ws_base}/api/agent/ws?key={quote(key)}&machine_id={quote(machine_id)}"


# ---------------------------------------------------------------------------
#  Agente
# ---------------------------------------------------------------------------
class ElekaAgent:
    def __init__(self, cfg: dict, simulate: bool = False, once: bool = False):
        self.cfg = cfg
        self.simulate = simulate
        self.once = once
        self.cloud_url = cfg["cloud_url"]
        self.key = cfg["license_key"]
        self.machine_id = cfg["machine_id"]
        self.account_id = account_id_for(self.key)

        # Estado de Facebook (solo en modo real).
        self._authenticator = None  # FacebookAuthenticator
        self._driver = None
        # Evento para reanudar tras aprobar el 2FA en el celular.
        self._twofa_event = None

        self._jobs_processed = 0
        self._stop = False

    # --- envio de mensajes ------------------------------------------------
    async def _send(self, ws, payload: dict) -> None:
        await ws.send(json.dumps(payload))

    async def _send_status(self, ws, state: str) -> None:
        await self._send(ws, {"type": "status", "state": state})

    # --- bucle principal con reconexion + backoff -------------------------
    async def run(self) -> None:
        # ws_url_base permite que el endpoint WebSocket viva en un host/puerto
        # distinto al de la API REST (opcional; por defecto se deriva de cloud_url).
        ws_base = self.cfg.get("ws_url")
        if ws_base:
            from urllib.parse import quote
            ws_url = (f"{ws_base.rstrip('/')}/api/agent/ws"
                      f"?key={quote(self.key)}&machine_id={quote(self.machine_id)}")
        else:
            ws_url = build_ws_url(self.cloud_url, self.key, self.machine_id)
        backoff = 1
        max_backoff = 60
        while not self._stop:
            try:
                print(f"Conectando al cloud: {self.cloud_url} (cuenta {self.account_id})")
                async with websockets.connect(ws_url, max_size=None) as ws:
                    backoff = 1  # reset al conectar bien
                    await self._on_connected(ws)
                    await self._listen(ws)
            except (websockets.ConnectionClosed, OSError) as e:
                print(f"Conexion perdida: {e}")
            except Exception as e:  # cierre por licencia invalida u otros
                # El relay cierra con code 4001 si la licencia no es valida.
                code = getattr(e, "code", None)
                if code == 4001:
                    print(f"El cloud rechazo la licencia: {getattr(e, 'reason', '')}. Saliendo.")
                    return
                print(f"Error de conexion: {e}")

            if self._stop:
                break
            print(f"Reintentando en {backoff}s...")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)

    async def _on_connected(self, ws) -> None:
        """Handshake: hello + status idle al conectar."""
        await self._send(ws, {
            "type": "hello",
            "machine_id": self.machine_id,
            "agent_version": AGENT_VERSION,
        })
        await self._send_status(ws, "idle")
        print("Conectado. Esperando jobs...")

    async def _listen(self, ws) -> None:
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except Exception:
                continue
            mtype = msg.get("type")
            if mtype == "ping":
                await self._send(ws, {"type": "pong"})
            elif mtype == "publish_job":
                await self._handle_job(ws, msg)
                if self.once:
                    self._stop = True
                    return
            elif mtype == "twofa_approved":
                # El dashboard avisa que el cliente aprobo el 2FA en el celular.
                if self._twofa_event is not None:
                    self._twofa_event.set()
            # Otros tipos se ignoran silenciosamente.

    # --- procesamiento de un job -----------------------------------------
    async def _handle_job(self, ws, msg: dict) -> None:
        job_id = msg.get("job_id", "")
        items = msg.get("items", []) or []
        settings = msg.get("settings", {}) or {}

        await self._send(ws, {"type": "job_accepted", "job_id": job_id})
        await self._send_status(ws, "busy")

        ok = 0
        fail = 0
        total = len(items)

        try:
            for item in items:
                page = item.get("page", 0)
                title = item.get("title", "")
                price = item.get("price", "")
                description = item.get("description", "")
                tags = item.get("tags", []) or []
                image_urls = item.get("image_urls", []) or []

                await self._send(ws, {
                    "type": "progress", "job_id": job_id, "page": page,
                    "message": f"Procesando '{title}'...", "level": "info",
                })

                # 1) Descargar imagenes a un temp local.
                local_images = await self._download_images(ws, job_id, page, image_urls)

                # 2) Publicar (real o simulado).
                if self.simulate:
                    result = await self._simulate_listing(ws, job_id, page, title)
                else:
                    result = await self._real_listing(
                        ws, job_id, page, title, description, price,
                        settings, local_images, tags,
                    )

                if result.get("status") == "success":
                    ok += 1
                else:
                    fail += 1

                await self._send(ws, {
                    "type": "item_done", "job_id": job_id, "page": page,
                    "status": result.get("status"), "title": title, "price": str(price),
                    "listing_url": result.get("listing_url"),
                    "error": result.get("error"),
                })

                # Limpiar temporales del item.
                self._cleanup_temp(local_images)
        finally:
            await self._send(ws, {
                "type": "job_done", "job_id": job_id, "ok": ok, "fail": fail, "total": total,
            })
            await self._send_status(ws, "idle")
            self._jobs_processed += 1

    # --- descarga de imagenes --------------------------------------------
    async def _download_images(self, ws, job_id, page, image_urls):
        """Descarga cada image_url (resuelta contra cloud_url) a un temp local."""
        paths = []
        if self.simulate:
            # No descargamos nada real; devolvemos rutas ficticias.
            return [f"<sim>/img_{i}.png" for i in range(len(image_urls))]

        for idx, rel in enumerate(image_urls):
            try:
                url = rel if rel.startswith(("http://", "https://")) else self.cloud_url.rstrip("/") + rel
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
                fd, tmp = tempfile.mkstemp(prefix=f"eleka_{job_id}_{page}_{idx}_", suffix=".jpg")
                with os.fdopen(fd, "wb") as f:
                    f.write(resp.content)
                paths.append(tmp)
            except Exception as e:
                await self._send(ws, {
                    "type": "progress", "job_id": job_id, "page": page,
                    "message": f"No se pudo descargar imagen {idx}: {e}", "level": "warn",
                })
        return paths

    def _cleanup_temp(self, paths):
        if self.simulate:
            return
        for p in paths:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass

    # --- flujo simulado (sin Chrome) -------------------------------------
    async def _simulate_listing(self, ws, job_id, page, title):
        await self._send(ws, {
            "type": "progress", "job_id": job_id, "page": page,
            "message": "[SIMULACION] Publicando en Facebook Marketplace...", "level": "info",
        })
        await asyncio.sleep(0.05)  # simula trabajo
        await self._send(ws, {
            "type": "progress", "job_id": job_id, "page": page,
            "message": "[SIMULACION] Publicacion completada.", "level": "info",
        })
        return {"status": "success", "listing_url": None, "error": None}

    # --- flujo real (Selenium) -------------------------------------------
    async def _ensure_login(self, ws, job_id, page):
        """Asegura login de Facebook reusando FacebookAuthenticator. Maneja 2FA."""
        if self._driver is not None:
            return True

        # Importes diferidos: solo se cargan en modo real (necesitan selenium, etc.).
        from modules.facebook_auth import FacebookAuthenticator

        # Credenciales: de config (opcionales) o por consola. Con perfil
        # persistente, normalmente la sesion ya esta guardada y no hacen falta.
        email = self.cfg.get("fb_email") or os.environ.get("ELEKA_FB_EMAIL", "")
        password = self.cfg.get("fb_password") or os.environ.get("ELEKA_FB_PASSWORD", "")
        twofa_secret = self.cfg.get("fb_2fa_secret") or os.environ.get("ELEKA_FB_2FA", "")

        await self._send(ws, {
            "type": "progress", "job_id": job_id, "page": page,
            "message": "Asegurando sesion de Facebook...", "level": "info",
        })

        # Callback de 2FA: emite status:need_2fa y espera la aprobacion.
        loop = asyncio.get_event_loop()
        self._twofa_event = asyncio.Event()

        def twofa_callback():
            # Llamado desde el hilo de Selenium: notifica al loop y bloquea hasta
            # que llegue 'twofa_approved' o pase un timeout largo.
            asyncio.run_coroutine_threadsafe(
                self._send_status(ws, "need_2fa"), loop
            )
            fut = asyncio.run_coroutine_threadsafe(
                asyncio.wait_for(self._twofa_event.wait(), timeout=300), loop
            )
            try:
                fut.result()
                return True
            except Exception:
                # Timeout sin aprobacion: degradar a False (login fallido).
                return False

        self._authenticator = FacebookAuthenticator(
            email=email,
            password=password,
            two_fa_secret=twofa_secret or None,
            headless=False,
            twofa_callback=twofa_callback,
            user_data_dir=str(CHROME_PROFILE_DIR),
        )

        await self._send_status(ws, "need_login")
        # El login bloquea (Selenium): lo corremos en un hilo aparte.
        driver = await loop.run_in_executor(None, self._authenticator.login)
        if driver is None:
            await self._send_status(ws, "logged_out")
            return False
        self._driver = driver
        await self._send_status(ws, "logged_in")
        return True

    async def _real_listing(self, ws, job_id, page, title, description, price,
                            settings, local_images, tags):
        from modules.marketplace_automation import MarketplaceAutomation

        loop = asyncio.get_event_loop()
        logged = await self._ensure_login(ws, job_id, page)
        if not logged:
            return {"status": "fail", "listing_url": None, "error": "login_failed"}

        category = settings.get("category")
        condition = settings.get("condition", "Nuevo")

        def _do_create():
            automation = MarketplaceAutomation(self._driver)
            return automation.create_listing(
                title=title,
                description=description,
                price=price,
                category=category,
                condition=condition,
                images=local_images,
                tags=tags,
            )

        await self._send(ws, {
            "type": "progress", "job_id": job_id, "page": page,
            "message": "Publicando en Facebook Marketplace...", "level": "info",
        })
        try:
            ok = await loop.run_in_executor(None, _do_create)
        except Exception as e:
            return {"status": "fail", "listing_url": None, "error": str(e)}

        if ok:
            return {"status": "success", "listing_url": None, "error": None}
        return {"status": "fail", "listing_url": None, "error": "create_listing_failed"}

    def close(self):
        if self._authenticator is not None:
            try:
                self._authenticator.close()
            except Exception:
                pass


# ---------------------------------------------------------------------------
#  Entry point
# ---------------------------------------------------------------------------
def main(argv=None):
    parser = argparse.ArgumentParser(description="ELEKA Marketplace - Agente local")
    parser.add_argument("--simulate", action="store_true",
                        help="ejecuta el flujo sin abrir Chrome (eventos simulados)")
    parser.add_argument("--once", action="store_true",
                        help="procesa un solo job y termina")
    parser.add_argument("--cloud-url", default=None,
                        help="sobrescribe la cloud_url de config")
    args = parser.parse_args(argv)

    cfg = load_config(cloud_url_override=args.cloud_url)
    print(f"ELEKA Marketplace Agent v{AGENT_VERSION}")
    print(f"  cloud_url : {cfg['cloud_url']}")
    print(f"  machine_id: {cfg['machine_id']}")
    print(f"  account_id: {account_id_for(cfg['license_key'])}")
    if args.simulate:
        print("  modo      : SIMULACION (no se abrira Chrome)")

    # 1) Validar licencia antes de conectar.
    try:
        result = validate_license(cfg["cloud_url"], cfg["license_key"], cfg["machine_id"])
    except Exception as e:
        print(f"No se pudo validar la licencia con el cloud: {e}")
        sys.exit(2)

    if not result.get("valid"):
        reason = result.get("reason", "desconocido")
        print(f"Licencia invalida (motivo: {reason}). Revisa tu clave o contacta a soporte.")
        sys.exit(3)

    print(f"Licencia valida. Plan: {result.get('plan')} | "
          f"limite diario: {result.get('daily_limit')} | expira: {result.get('expires_at')}")

    # 2) Conectar y atender jobs.
    agent = ElekaAgent(cfg, simulate=args.simulate, once=args.once)
    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        print("\nAgente detenido por el usuario.")
    finally:
        agent.close()


if __name__ == "__main__":
    main()
