"""
Autotest del agente ELEKA Marketplace (modo simulacion).

Levanta:
  1. Un servidor HTTP falso que responde POST /api/license/validate con valid:true.
  2. Un relay WebSocket falso que valida el handshake (hello + status), manda un
     publish_job de prueba y verifica que el agente responde con la secuencia
     correcta: job_accepted, progress, item_done(success), job_done.

Lanza el agente como subproceso con --simulate --once apuntando al servidor local,
de modo que NO se abre Chrome ni se toca Facebook.

Imprime PASS/FAIL y devuelve codigo de salida 0/1.
"""
import asyncio
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import websockets

HERE = os.path.dirname(os.path.abspath(__file__))
AGENT_PY = os.path.join(HERE, "agent.py")

# La libreria websockets solo acepta GET en el handshake, asi que servimos la
# validacion de licencia (HTTP POST) en un puerto aparte (stdlib HTTPServer) y el
# relay WebSocket en otro. La config de prueba apunta cloud_url al puerto de
# licencia y usa la opcion ws_url para el puerto del relay.
HTTP_PORT = 8771
WS_PORT = 8772

# Config de prueba (no toca la config real del usuario): usamos un HOME temporal.
TEST_KEY = "ELEKA-MKT-TEST-TEST-TEST"


# ---------------------------------------------------------------------------
#  Servidor HTTP falso: /api/license/validate
# ---------------------------------------------------------------------------
class LicenseHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # silenciar logs

    def do_POST(self):
        if self.path == "/api/license/validate":
            length = int(self.headers.get("Content-Length", 0))
            _ = self.rfile.read(length)
            body = json.dumps({
                "valid": True,
                "account_id": "testaccount0001",
                "plan": "basic",
                "expires_at": None,
                "daily_limit": 20,
                "reason": "ok",
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()


def start_http_server():
    server = HTTPServer(("127.0.0.1", HTTP_PORT), LicenseHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


# ---------------------------------------------------------------------------
#  Relay WebSocket falso
# ---------------------------------------------------------------------------
class RelayResult:
    def __init__(self):
        self.events = []          # mensajes recibidos del agente
        self.handshake_ok = False
        self.done = asyncio.Event()


async def relay_handler(ws, result: RelayResult):
    # 1) Validar handshake: esperamos 'hello' y 'status'.
    got_hello = False
    got_status = False
    for _ in range(2):
        raw = await asyncio.wait_for(ws.recv(), timeout=10)
        msg = json.loads(raw)
        result.events.append(msg)
        if msg.get("type") == "hello" and msg.get("machine_id"):
            got_hello = True
        elif msg.get("type") == "status" and msg.get("state") == "idle":
            got_status = True
    result.handshake_ok = got_hello and got_status

    # 2) Enviar un publish_job de prueba.
    job = {
        "type": "publish_job",
        "job_id": "j_test01",
        "items": [{
            "page": 1,
            "title": "Producto de prueba",
            "price": "15",
            "description": "Descripcion de prueba",
            "tags": ["a", "b"],
            "image_urls": ["/api/jobs/j_test01/img/0"],
        }],
        "settings": {"category": "Otros", "condition": "Nuevo"},
    }
    await ws.send(json.dumps(job))

    # 3) Recoger eventos hasta job_done.
    try:
        while True:
            raw = await asyncio.wait_for(ws.recv(), timeout=15)
            msg = json.loads(raw)
            result.events.append(msg)
            if msg.get("type") == "job_done":
                break
    except (asyncio.TimeoutError, websockets.ConnectionClosed):
        pass
    finally:
        result.done.set()


async def run_relay(result: RelayResult):
    async def handler(ws):
        await relay_handler(ws, result)

    server = await websockets.serve(handler, "127.0.0.1", WS_PORT, max_size=None)
    return server


# ---------------------------------------------------------------------------
#  Verificacion de la secuencia de eventos
# ---------------------------------------------------------------------------
def verify(result: RelayResult) -> bool:
    ok = True

    def check(cond, label):
        nonlocal ok
        status = "PASS" if cond else "FAIL"
        print(f"  [{status}] {label}")
        if not cond:
            ok = False

    types = [e.get("type") for e in result.events]
    check(result.handshake_ok, "handshake: hello + status idle recibidos")

    check("job_accepted" in types, "se recibio job_accepted")
    ja = next((e for e in result.events if e.get("type") == "job_accepted"), {})
    check(ja.get("job_id") == "j_test01", "job_accepted con job_id correcto")

    check(any(e.get("type") == "progress" for e in result.events),
          "se recibio al menos un progress")

    item = next((e for e in result.events if e.get("type") == "item_done"), {})
    check(bool(item), "se recibio item_done")
    check(item.get("status") == "success", "item_done con status success")
    check(item.get("page") == 1, "item_done con page correcta")
    check(item.get("title") == "Producto de prueba", "item_done con title correcto")

    jd = next((e for e in result.events if e.get("type") == "job_done"), {})
    check(bool(jd), "se recibio job_done")
    check(jd.get("ok") == 1, "job_done ok=1")
    check(jd.get("fail") == 0, "job_done fail=0")
    check(jd.get("total") == 1, "job_done total=1")

    return ok


# ---------------------------------------------------------------------------
#  Orquestacion del test
# ---------------------------------------------------------------------------
async def main():
    print("== Autotest agente ELEKA Marketplace (modo simulacion) ==")

    # HOME temporal para no tocar la config real del usuario.
    import tempfile
    tmp_home = tempfile.mkdtemp(prefix="eleka_test_home_")
    env = dict(os.environ)
    env["USERPROFILE"] = tmp_home
    env["HOME"] = tmp_home

    # Pre-sembrar config con clave para que el agente no pida input por consola.
    cfg_dir = os.path.join(tmp_home, ".eleka-marketplace")
    os.makedirs(cfg_dir, exist_ok=True)
    with open(os.path.join(cfg_dir, "config.json"), "w", encoding="utf-8") as f:
        json.dump({
            "cloud_url": f"http://127.0.0.1:{HTTP_PORT}",
            "ws_url": f"ws://127.0.0.1:{WS_PORT}",
            "license_key": TEST_KEY,
            "machine_id": "test-machine-0001",
        }, f)

    http_server = start_http_server()
    result = RelayResult()
    ws_server = await run_relay(result)

    # Lanzar el agente como subproceso.
    cmd = [
        sys.executable, AGENT_PY,
        "--simulate", "--once",
        "--cloud-url", f"http://127.0.0.1:{HTTP_PORT}",
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd, env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    try:
        await asyncio.wait_for(result.done.wait(), timeout=30)
    except asyncio.TimeoutError:
        print("  [FAIL] timeout esperando job_done del agente")

    # Cerrar todo.
    ws_server.close()
    await ws_server.wait_closed()
    http_server.shutdown()
    # Leer la salida del agente ANTES de matarlo (para no perderla en timeouts).
    agent_out = b""
    try:
        agent_out = await asyncio.wait_for(proc.stdout.read(), timeout=3)
    except asyncio.TimeoutError:
        pass
    except Exception:
        pass

    try:
        proc.terminate()
        await asyncio.wait_for(proc.wait(), timeout=5)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass

    if agent_out:
        print("\n--- salida del agente ---")
        print(agent_out.decode(errors="replace").strip())
        print("--- fin salida ---\n")

    print("Resultados:")
    passed = verify(result)
    print()
    print("RESULTADO FINAL:", "PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
