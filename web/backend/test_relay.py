"""
Autotest del relay (ELEKA Marketplace) - Agente 2
=================================================
Arranca una app FastAPI en memoria con SOLO el router del relay incluido y
verifica el contrato end-to-end usando el TestClient de Starlette (soporta REST
y WebSocket de forma sincrona):

  CASO 1  Handshake del agente: se conecta por WS y queda "online".
  CASO 2  Publish con agente online: el agente recibe publish_job con
          image_files convertidos a image_urls.
  CASO 3  Reenvio de eventos: progress / item_done / job_done emitidos por el
          agente llegan al WS del dashboard /api/jobs/ws/{job_id}.
  CASO 4  Agente offline: el job queda "queued" y se entrega al conectar.
  CASO 5  Servir imagen: /api/jobs/{job_id}/img/{idx} devuelve los bytes.

Ejecutar:
    set RELAY_ALLOW_INSECURE=1   (Windows)  /  export RELAY_ALLOW_INSECURE=1
    python web/backend/test_relay.py

Usa RELAY_ALLOW_INSECURE=1 para que el stub de licencias acepte la clave de
prueba sin necesitar el modulo real licensing.py.
"""
import os
import sys
from pathlib import Path

# Aseguramos el flag ANTES de importar relay (lo lee al validar la licencia).
os.environ["RELAY_ALLOW_INSECURE"] = "1"

# Permitir importar relay tanto si se corre desde la raiz como desde web/backend.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI                  # noqa: E402
from fastapi.testclient import TestClient    # noqa: E402

import relay  # noqa: E402

MACHINE = "test-machine-001"


def _obtain_key() -> str:
    """Obtiene una clave valida para el autotest.

    - Si el modulo real `licensing` esta presente, creamos una licencia real en
      la BD (probamos contra la implementacion real, no solo el stub).
    - Si solo esta el stub (RELAY_ALLOW_INSECURE=1), cualquier clave no vacia vale.
    """
    if relay._LICENSING_REAL:
        try:
            import licensing  # noqa
            info = licensing.create_license(plan="basic", days=30, daily_limit=20,
                                            notes="autotest_relay")
            return info["key"]
        except Exception as e:
            print(f"[WARN] No se pudo crear licencia real ({e}); uso clave de stub")
    return "ELEKA-MKT-TEST-TEST-TEST"


KEY = _obtain_key()

_results = []


def check(name: str, ok: bool, detail: str = ""):
    _results.append(ok)
    estado = "PASS" if ok else "FAIL"
    extra = f"  ({detail})" if detail else ""
    print(f"[{estado}] {name}{extra}")


def reset_state():
    """Estado limpio entre casos."""
    relay.AGENTS.clear()
    relay.JOBS.clear()
    relay.SUBS.clear()
    relay.QUEUE.clear()


def make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(relay.router)
    return app


def _publish_payload():
    return {
        "account_id": relay.account_id_for(KEY),
        "items": [{
            "page": 1,
            "title": "Audifonos Bluetooth",
            "price": "15",
            "description": "Producto de prueba",
            "tags": ["audio", "bluetooth"],
            "image_files": ["img_test_a.png", "img_test_b.png"],
        }],
        "settings": {"category": "Otros", "condition": "Nuevo"},
    }


def test_online_publish_and_forward(app):
    """CASO 1, 2 y 3: agente online -> publish -> forward de eventos."""
    client = TestClient(app)
    with client.websocket_connect(f"/api/agent/ws?key={KEY}&machine_id={MACHINE}") as agent:
        agent.send_json({"type": "hello", "machine_id": MACHINE, "agent_version": "1.0.0"})

        # CASO 1: online
        acc = relay.account_id_for(KEY)
        r = client.get(f"/api/agent/online?account_id={acc}")
        check("CASO 1 agente online tras conectar", r.json().get("online") is True,
              f"online={r.json()}")

        # CASO 2: publish con agente online -> dispatched
        r = client.post("/api/jobs/publish", json=_publish_payload())
        body = r.json()
        job_id = body.get("job_id")
        check("CASO 2a publish devuelve dispatched", body.get("status") == "dispatched",
              f"status={body.get('status')}")

        # El agente recibe publish_job con image_urls
        msg = agent.receive_json()
        urls = msg["items"][0].get("image_urls", [])
        expected = [f"/api/jobs/{job_id}/img/0", f"/api/jobs/{job_id}/img/1"]
        check("CASO 2b agente recibe publish_job", msg.get("type") == "publish_job",
              f"type={msg.get('type')}")
        check("CASO 2c image_files -> image_urls absolutas", urls == expected,
              f"urls={urls}")
        check("CASO 2d no se filtran image_files al agente",
              "image_files" not in msg["items"][0])

        # CASO 3: el dashboard se suscribe y recibe los eventos del agente
        with client.websocket_connect(f"/api/jobs/ws/{job_id}") as dash:
            sub = dash.receive_json()  # mensaje "subscribed"
            check("CASO 3a dashboard recibe subscribed", sub.get("type") == "subscribed",
                  f"msg={sub}")

            agent.send_json({"type": "job_accepted", "job_id": job_id})
            ev = dash.receive_json()
            check("CASO 3b job_accepted llega al dashboard", ev.get("type") == "job_accepted")

            agent.send_json({"type": "progress", "job_id": job_id, "page": 1,
                             "message": "Publicando...", "level": "info"})
            ev = dash.receive_json()
            check("CASO 3c progress llega al dashboard",
                  ev.get("type") == "progress" and ev.get("message") == "Publicando...")

            agent.send_json({"type": "item_done", "job_id": job_id, "page": 1,
                             "status": "success", "title": "Audifonos Bluetooth",
                             "price": "15", "listing_url": None, "error": None})
            ev = dash.receive_json()
            check("CASO 3d item_done llega al dashboard",
                  ev.get("type") == "item_done" and ev.get("status") == "success")

            agent.send_json({"type": "job_done", "job_id": job_id, "ok": 1, "fail": 0, "total": 1})
            ev = dash.receive_json()
            check("CASO 3e job_done llega al dashboard",
                  ev.get("type") == "job_done" and ev.get("ok") == 1)
            check("CASO 3f job marcado como done",
                  relay.JOBS[job_id]["status"] == "done",
                  f"status={relay.JOBS[job_id]['status']}")

        # CASO 5: servir imagen (creamos los archivos de prueba en temp_images)
        for fn in ("img_test_a.png", "img_test_b.png"):
            (relay.TEMP_DIR / fn).write_bytes(b"PNGDATA-" + fn.encode())
        r = client.get(f"/api/jobs/{job_id}/img/0")
        check("CASO 5a sirve imagen idx 0",
              r.status_code == 200 and r.content == b"PNGDATA-img_test_a.png",
              f"code={r.status_code}")
        r = client.get(f"/api/jobs/{job_id}/img/1")
        check("CASO 5b sirve imagen idx 1",
              r.status_code == 200 and r.content == b"PNGDATA-img_test_b.png")
        r = client.get(f"/api/jobs/{job_id}/img/9")
        check("CASO 5c idx fuera de rango -> 404", r.status_code == 404,
              f"code={r.status_code}")

    # limpiar archivos de prueba
    for fn in ("img_test_a.png", "img_test_b.png"):
        try:
            (relay.TEMP_DIR / fn).unlink()
        except OSError:
            pass


def test_offline_queue(app):
    """CASO 4: agente offline -> job queued -> se entrega al conectar."""
    client = TestClient(app)
    acc = relay.account_id_for(KEY)

    r = client.get(f"/api/agent/online?account_id={acc}")
    check("CASO 4a agente offline antes de conectar", r.json().get("online") is False)

    r = client.post("/api/jobs/publish", json=_publish_payload())
    body = r.json()
    job_id = body.get("job_id")
    check("CASO 4b publish sin agente -> queued", body.get("status") == "queued",
          f"status={body.get('status')}")
    check("CASO 4c job en la cola de la cuenta",
          job_id in relay.QUEUE.get(acc, []))

    # Ahora conecta el agente: debe recibir el job encolado de inmediato.
    with client.websocket_connect(f"/api/agent/ws?key={KEY}&machine_id={MACHINE}") as agent:
        msg = agent.receive_json()
        check("CASO 4d job encolado se entrega al conectar",
              msg.get("type") == "publish_job" and msg.get("job_id") == job_id,
              f"type={msg.get('type')} job={msg.get('job_id')}")
        check("CASO 4e cola vaciada tras entregar",
              not relay.QUEUE.get(acc),
              f"queue={relay.QUEUE.get(acc)}")
        check("CASO 4f job pasa a dispatched",
              relay.JOBS[job_id]["status"] == "dispatched",
              f"status={relay.JOBS[job_id]['status']}")


def test_invalid_license(app):
    """Extra: licencia vacia debe rechazar la conexion del agente."""
    client = TestClient(app)
    rechazado = False
    try:
        with client.websocket_connect("/api/agent/ws?key=&machine_id=x") as agent:
            # Si el server cierra con 4001, receive_json lanzara excepcion.
            agent.receive_json()
    except Exception:
        rechazado = True
    check("EXTRA licencia vacia rechazada", rechazado)


def main():
    print("=" * 60)
    print("Autotest relay.py - ELEKA Marketplace (Agente 2)")
    print(f"licensing real importado: {relay._LICENSING_REAL}")
    print("=" * 60)

    reset_state()
    test_online_publish_and_forward(make_app())

    reset_state()
    test_offline_queue(make_app())

    reset_state()
    test_invalid_license(make_app())

    total = len(_results)
    passed = sum(1 for x in _results if x)
    print("=" * 60)
    print(f"RESULTADO: {passed}/{total} casos PASS")
    print("=" * 60)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
