# ELEKA Marketplace - Agente local

Agente que corre en la PC del cliente. Abre una conexion WebSocket **saliente**
hacia el cloud (eleka.me), recibe jobs de publicacion y los ejecuta con Selenium
contra Facebook Marketplace usando la cuenta y la IP del cliente.

La publicacion real a Facebook ocurre SIEMPRE aqui, en la PC del cliente. La IA
(Gemini) y el dashboard viven en el cloud. Ver `docs/HYBRID_CONTRACT.md` para el
protocolo completo.

## Requisitos del cliente

- Windows.
- **Google Chrome instalado** (el `chromedriver` se descarga solo en runtime via
  `webdriver-manager`).
- Una **clave de licencia** valida con formato `ELEKA-MKT-XXXX-XXXX-XXXX`.
- Conexion a internet (salida HTTPS/WSS hacia el cloud).

No hace falta tener Python instalado si se usa el `.exe` empaquetado.

## Configuracion

La configuracion se guarda en:

    %USERPROFILE%\.eleka-marketplace\config.json

Ejemplo:

    {
      "cloud_url": "https://market.eleka.me",
      "license_key": "ELEKA-MKT-XXXX-XXXX-XXXX",
      "machine_id": "<uuid generado y persistido>"
    }

- Si falta `license_key`, el agente la **pide por consola** la primera vez y la
  guarda.
- `ws_url` es **opcional**: solo para despliegues donde el endpoint WebSocket vive
  en otro host/puerto que la API REST. Por defecto se deriva de `cloud_url`.
- `machine_id` es un UUID generado y persistido automaticamente (1 licencia = 1 PC).
- El perfil de Chrome (sesion de Facebook persistente, evita re-loguear y repetir
  2FA) se guarda en `%USERPROFILE%\.eleka-marketplace\chrome-profile`.

Credenciales de Facebook (opcionales; con el perfil persistente normalmente NO se
necesitan tras el primer login): se pueden poner en `config.json` como
`fb_email`, `fb_password`, `fb_2fa_secret`, o via variables de entorno
`ELEKA_FB_EMAIL`, `ELEKA_FB_PASSWORD`, `ELEKA_FB_2FA`. Nunca se hardcodean.

## Ejecutar

### Modo simulacion (recomendado para probar la conexion sin Facebook)

No abre Chrome ni toca Facebook; recorre todo el protocolo emitiendo eventos de
exito simulados. Ideal para validar el handshake con el cloud.

    python agent.py --simulate

Con el `.exe`:

    ElekaMarketplaceAgent.exe --simulate

### Modo real (publica en Facebook)

    python agent.py
    # o
    ElekaMarketplaceAgent.exe

La primera vez abrira Chrome para iniciar sesion en Facebook. Si se requiere 2FA,
el agente emite `status:need_2fa` y espera a que apruebes desde tu celular.

### Flags

- `--simulate` : recorre el flujo sin abrir Chrome (eventos simulados).
- `--once`     : procesa un solo job y termina (util para pruebas).
- `--cloud-url`: sobrescribe la `cloud_url` de la config (util en pruebas locales).

## Autotest

`test_agent.py` levanta un servidor de licencias falso y un relay WebSocket falso
en `localhost`, lanza el agente en `--simulate --once` y verifica que responda con
`job_accepted`, `progress`, `item_done` y `job_done` correctos. **No toca Facebook.**

    pip install websockets requests
    python test_agent.py

Imprime `RESULTADO FINAL: PASS` o `FAIL`.

## Construir el .exe

Necesita Python 3.x en la maquina de build (no en la del cliente).

    powershell -ExecutionPolicy Bypass -File .\build.ps1

Genera `agent\dist\ElekaMarketplaceAgent.exe` (un unico archivo). Internamente:

- Crea un venv en `agent\.venv`.
- Instala `requirements.txt` + PyInstaller.
- Empaqueta con `--onefile --name ElekaMarketplaceAgent`, incluyendo
  `src/modules` y `src/config` del repo como datos.

Alternativa equivalente con el spec:

    pyinstaller agent.spec

## Como reutiliza el codigo existente

El agente NO reimplementa la automatizacion. Anade `<repo>/src` a `sys.path`
(igual que `web/backend/main.py`) e importa:

- `modules.facebook_auth.FacebookAuthenticator` - login + 2FA + perfil persistente.
- `modules.marketplace_automation.MarketplaceAutomation` - `create_listing(...)`.
- `modules.human` - delays humanos (usado por los modulos anteriores).

En el `.exe`, esos modulos se empaquetan como datos y se cargan desde el directorio
temporal de PyInstaller (`sys._MEIPASS/src`).
