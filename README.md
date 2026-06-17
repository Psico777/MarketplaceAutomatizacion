# 🚀 Facebook Marketplace Automation

Sistema automatizado con interfaz gráfica para subir productos a Facebook Marketplace.

## ⚡ Características

- ✅ **Interfaz Gráfica**: Vista previa de imágenes, selección individual
- ✅ **Análisis IA**: Google Gemini para descripciones automáticas
- ✅ **Responder 24/7**: contesta los chats de Messenger con IA, a intervalos
  ALEATORIOS de 3-8 min (no satura ni delata el bot)
- ✅ **Grupos**: publica en grupos de Facebook y se une a grupos
- ✅ **Comportamiento humano**: tipeo, pausas y clicks aleatorios (`utils/human.py`)
- ✅ **Sesión persistente**: perfil de Chrome reutilizable (no re-2FA cada vez)
- ✅ **Headless**: corre sin pantalla en Raspberry Pi 5 / DigitalOcean droplet
- ✅ **Caché Inteligente**: No re-analiza imágenes ya procesadas

## 🚀 Uso Rápido

```bash
# Interfaz grafica (subir productos desde PDF)
python launch_gui.py

# Responder automatico de Messenger (IA, cada 3-8 min)
python run_responder.py              # envia de verdad
python run_responder.py --dry-run    # prueba: genera pero NO envia

# Grupos de Facebook
python run_groups.py join                                   # unirse a grupos
python run_groups.py post --text "GENTE LLEGARON ... <3"    # publicar
python run_groups.py post --text-file mensaje.txt --images temp_images/1.jpg
```

> ⚠️ Automatizar Facebook/Messenger puede violar sus Términos. Úsalo bajo tu
> responsabilidad, solo en tu propia cuenta/negocio, y con tiempos prudentes.

### Pasos:
1. 📄 **Cargar PDF** → Seleccionar tu PDF de productos
2. ✓ **Marcar productos** → Checkbox de los que quieres subir
3. 🔐 **Login Facebook** → Aprobar 2FA en celular
4. 🚀 **Subir** → Click "Subir Seleccionados"

## ⚙️ Configuración

Editar `src/config/settings.py`:

```python
FACEBOOK_EMAIL = "tu_email@example.com"
FACEBOOK_PASSWORD = "tu_password"
GEMINI_API_KEY = "tu_api_key_gemini"
```

## 📁 Estructura

```
MarketplaceAutomatizacion/
├── launch_gui.py              # 🚀 Launcher GUI
├── run_responder.py           # 🤖 Responder de Messenger (24/7)
├── run_groups.py              # 👥 Unirse / publicar en grupos
├── marketplace_gui.py         # 🖼️ Interfaz gráfica
├── src/
│   ├── modules/
│   │   ├── ai_analyzer.py            # 🤖 Análisis IA + generate_reply()
│   │   ├── marketplace_automation.py # ⚡ Subida de productos
│   │   ├── messenger_responder.py    # 💬 Responder automático IA
│   │   ├── group_poster.py           # 👥 Publicar/unirse a grupos
│   │   ├── facebook_auth.py          # 🔐 Login 2FA + perfil persistente
│   │   └── pdf_extractor.py          # 📄 Extracción PDFs
│   ├── utils/human.py         # 🎭 Pausas/tipeo/clicks humanos
│   └── config/settings.py     # ⚙️ Configuración
└── ai_analysis_cache.json     # 💾 Caché (auto-generado)
```

## 🖥️ Despliegue sin pantalla (Raspberry Pi 5 / DigitalOcean)

```bash
# 1) Configura el .env (copia .env.example) con:
HEADLESS=True
CHROME_PROFILE_DIR=/home/USUARIO/.fb_profile   # sesion persistente

# 2) Primer login (una sola vez) para guardar la sesion en el perfil.
#    En el Pi puedes hacerlo con pantalla, o aprobar el 2FA en el celular.
python run_responder.py --rounds 1

# 3) Dejalo corriendo 24/7 (ej. con nohup o un servicio systemd):
nohup python run_responder.py > responder.log 2>&1 &
```

En **DigitalOcean** (droplet sin GPU): instala `chromium-browser` y
`chromium-chromedriver`, define `CHROME_BINARY=/usr/bin/chromium-browser` y
`CHROMEDRIVER_PATH=/usr/bin/chromedriver`. Todo va en modo `--headless=new`.

## ⚡ Optimizaciones

- **Timeouts**: 0.1-0.2s (antes 5s)
- **Velocidad**: ~30-40s por producto (antes 60s)
- **Caché IA**: 95% más rápido en re-análisis
- **Threading**: UI nunca se congela

## 📋 Formato de Descripción

```
GENTE LLEGARON LOS [PRODUCTO] AL MEJOR PRECIO <3

:) 1 unidad x 14 soles
:D 3 unidades a mas x 9 soles (27 soles)

---
(todas las compras por mayor salen a partir de la media docena)

SOMOS LK <3
Contacto: 995665397 WhatsApp
```

## 📞 Contacto

**SOMOS LK** <3  
WhatsApp: 995665397

---

**Versión**: 2.0 Final  
**Última actualización**: Nov 6, 2025
