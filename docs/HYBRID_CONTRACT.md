# ELEKA Marketplace — Contrato de integración (modelo híbrido)

Arquitectura: **Dashboard web (cloud) + Agente local (.exe en la PC del cliente)**.
El agente abre una conexión **saliente** (WebSocket) hacia el cloud; el cloud actúa
de **relay** entre el dashboard y el agente. El post a Facebook lo ejecuta SIEMPRE
el agente en la PC del cliente, con su IP y su cuenta. La IA (Gemini) corre en el cloud.

```
NAVEGADOR ──HTTPS──► CLOUD (eleka.me) ◄──WS saliente── AGENTE (.exe en PC cliente)
 dashboard           FastAPI + relay                    Chrome local + cuenta del cliente
```

Este documento es la ÚNICA fuente de verdad del protocolo. Las 3 piezas deben
respetarlo al pie de la letra para encajar sin tocarse entre sí.

---

## 0. Identidad de cuenta (routing)

Tanto la API de licencias como el relay derivan el id de cuenta IGUAL:

```python
import hashlib
def account_id_for(key: str) -> str:
    return hashlib.sha256(key.strip().encode()).hexdigest()[:16]
```

`account_id` es lo que enlaza: licencia ↔ agente conectado ↔ jobs del dashboard.

## 1. Formato de clave de licencia

- Patrón: `ELEKA-MKT-XXXX-XXXX-XXXX` (4 grupos alfanuméricos MAYÚSCULAS, sin 0/O/1/I para evitar confusión).
- En la BD se guarda SOLO el `sha256(key)` (nunca la clave en claro).
- BD: SQLite stdlib (`sqlite3`) en `web/backend/licenses.db`, tabla:
  `licenses(key_hash TEXT PRIMARY KEY, account_id TEXT, plan TEXT, status TEXT,
            machine_id TEXT, created_at TEXT, expires_at TEXT, daily_limit INTEGER, notes TEXT)`
  - `status`: `active` | `revoked`.
  - `machine_id`: NULL hasta el primer `validate`; luego queda fijado (1 licencia = 1 PC).
  - `daily_limit`: máximo de publicaciones/día que el plan permite (default 20).

## 2. API de licencias (cloud)  — DUEÑO: Agente 1

Router FastAPI en `web/backend/licensing.py`, prefijo `/api/license`. Self-contained
(no importa nada de `main.py`). Expone también funciones importables por el relay.

REST:
- `POST /api/license/validate`  body `{ "key": "...", "machine_id": "..." }`
  → `{ "valid": bool, "account_id": "...", "plan": "...", "expires_at": "ISO|null",
       "daily_limit": int, "reason": "ok|not_found|revoked|expired|machine_mismatch" }`
  Reglas: si la clave existe, está `active`, no expiró, y (machine_id no fijado o coincide)
  → `valid:true` y fija machine_id si estaba NULL. Si no, `valid:false` con `reason`.
- `GET /api/license/status`  header `X-License-Key: <key>` → mismo shape sin tocar machine_id.

Admin (header `X-Admin-Token` == env `ELEKA_ADMIN_TOKEN`; si no coincide → 401):
- `POST /api/license/admin/create` body `{ "plan":"basic", "days":30, "daily_limit":20, "notes":"" }`
  → `{ "key":"ELEKA-MKT-....", "account_id":"...", "expires_at":"ISO" }`  (la clave en claro se devuelve SOLO aquí, una vez)
- `GET  /api/license/admin/list` → lista (sin claves en claro: key_hash parcial, account_id, plan, status, expires_at, machine_id)
- `POST /api/license/admin/revoke` body `{ "key": "..." }` → `{ "ok": true }`

Funciones importables (las usa el relay):
```python
def validate_key(key: str, machine_id: str | None = None) -> dict   # mismo dict que /validate
def account_id_for(key: str) -> str
```

CLI de administración: `web/backend/manage_licenses.py` (crear/listar/revocar desde consola).

## 3. Relay + cola de jobs (cloud)  — DUEÑO: Agente 2

Router FastAPI en `web/backend/relay.py`, self-contained (NO toca `main.py`).
Importa de `licensing` SOLO `validate_key` y `account_id_for`. Estado en memoria:
`AGENTS: dict[account_id, WebSocket]`, `JOBS: dict[job_id, dict]`, `SUBS: dict[job_id, list[WebSocket]]`,
y una cola por cuenta para jobs cuando el agente está offline.

Imágenes: el dashboard ya subió las fotos al cloud vía el endpoint existente
`/api/upload-images` (quedan en `web/backend/temp_images/<filename>`). Los jobs llevan
esos `image_files` (nombres) y el relay se las sirve al agente.

WebSocket del AGENTE (saliente desde la PC):
- `GET /api/agent/ws?key=<license>&machine_id=<id>`
  Al conectar: `validate_key(key, machine_id)`. Si `valid:false` → cerrar con code 4001 y `reason`.
  Si ok: registrar `AGENTS[account_id]=ws`, y despachar jobs encolados de esa cuenta.

Lado DASHBOARD:
- `POST /api/jobs/publish` body
  `{ "account_id":"...", "items":[ {"page":1,"title":"...","price":"15","description":"...","tags":[...],"image_files":["img_x.png"]} ], "settings":{"category":"...","condition":"Nuevo"} }`
  → `{ "job_id":"...", "status":"dispatched|queued|no_agent" }` (queued si agente offline; no_agent si prefieres rechazar — usa queued).
- `GET /api/jobs/ws/{job_id}`  WebSocket: reenvía al dashboard los eventos de progreso del job.
- `GET /api/agent/online?account_id=...` → `{ "online": bool }`
- `GET /api/jobs/{job_id}/img/{idx}`  → devuelve los bytes de `image_files[idx]` desde `temp_images/` (lo usa el agente para descargar las fotos).

### Mensajes WebSocket (JSON) — compartidos por Agente 2 y Agente 3

Cloud → Agente:
```json
{"type":"publish_job","job_id":"j_ab12","items":[
  {"page":1,"title":"...","price":"15","description":"...","tags":["a","b"],
   "image_urls":["/api/jobs/j_ab12/img/0"]}],
 "settings":{"category":"Otros","condition":"Nuevo"}}
{"type":"ping"}
```
(El relay convierte `image_files` → `image_urls` absolutas en el mensaje al agente.)

Agente → Cloud:
```json
{"type":"hello","machine_id":"...","agent_version":"1.0.0"}
{"type":"status","state":"idle|busy|need_login|need_2fa|logged_in|logged_out"}
{"type":"job_accepted","job_id":"j_ab12"}
{"type":"progress","job_id":"j_ab12","page":1,"message":"Publicando...","level":"info"}
{"type":"item_done","job_id":"j_ab12","page":1,"status":"success","title":"...","price":"15","listing_url":null,"error":null}
{"type":"job_done","job_id":"j_ab12","ok":1,"fail":0,"total":1}
{"type":"pong"}
```
El relay reenvía TODO `progress|item_done|job_done|status` a los `SUBS[job_id]` (dashboard).

## 4. Agente local (.exe)  — DUEÑO: Agente 3

Carpeta nueva `agent/` en la raíz del repo: `agent/agent.py`, `agent/requirements.txt`,
`agent/build.ps1`, `agent/agent.spec`, `agent/README.md`.

Comportamiento:
1. Config local en `%USERPROFILE%/.eleka-marketplace/config.json`
   `{ "cloud_url":"https://market.eleka.me", "license_key":"ELEKA-MKT-...", "machine_id":"<uuid persistido>" }`.
   Si falta la clave, pedirla por consola la primera vez y guardarla. `machine_id` = uuid4 persistido.
2. Validar licencia vía `POST {cloud_url}/api/license/validate`. Si `valid:false` → mensaje claro y salir.
3. Conectar `wss://.../api/agent/ws?key=...&machine_id=...` con reconexión + backoff. Responder `ping`→`pong`.
4. Al recibir `publish_job`: enviar `job_accepted`; descargar cada `image_urls` a un temp local;
   asegurar login de Facebook (reusar `FacebookAuthenticator` con perfil persistente en
   `%USERPROFILE%/.eleka-marketplace/chrome-profile`); por cada item llamar
   `MarketplaceAutomation.create_listing(...)`, emitiendo `progress` e `item_done`; al final `job_done`.
   Si requiere 2FA, emitir `status:need_2fa` y esperar aprobación en el celular del cliente.
5. Reusar el código existente: añadir `<repo>/src` a `sys.path` (igual que `web/backend/main.py`)
   e importar `modules.facebook_auth`, `modules.marketplace_automation`, `modules.human`.
6. Flag `--simulate`: ejecuta el flujo SIN abrir Chrome (emite eventos simulando éxito) para
   probar el handshake/relay end-to-end sin Facebook. ÚSALO para tu autotest.
7. Empaquetado: `build.ps1` → PyInstaller `--onefile --name ElekaMarketplaceAgent`, incluyendo
   `src/modules` como datos/hidden-imports. Chrome del cliente + chromedriver vía webdriver-manager en runtime.

## 5. Reglas de oro (para no chocar entre agentes)

- Cada agente crea SOLO sus archivos (sección "DUEÑO"). NADIE edita `web/backend/main.py`
  (la integración `app.include_router(...)` la hace el orquestador al final).
- Self-contained: el relay importa de `licensing` solo las 2 funciones indicadas. El agente .exe
  no importa nada del backend web.
- NADA de claves/secretos hardcodeados. `ELEKA_ADMIN_TOKEN` y `cloud_url` por entorno/config.
- Sin emojis en código ni en UIs.
- Incluir un autotest ejecutable por componente y CORRERLO si hay Python disponible
  (`py -3` o `python`), reportando el resultado. Si no hay Python local, validar por revisión.
- La publicación real a Facebook NUNCA corre en el cloud; solo en el agente local.
