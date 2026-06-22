# Facebook Marketplace Automation — LK

Sistema para publicar **tus propios productos** en Facebook Marketplace a partir de un PDF,
con análisis por IA (Google Gemini). Disponible en dos modos:

- 🖥️ **Escritorio** (Tkinter) — `python launch_gui.py`
- 🌐 **Web** (FastAPI + React) — apartado `web/`, mismo estilo que el resto de productos LK

> ⚠️ Automatizar Facebook puede violar sus Términos. Úsalo **solo con tu cuenta y tus productos**, bajo tu responsabilidad.

## ✨ Características

- **PDF → imágenes** y selección visual de los productos a subir
- **IA (Gemini)**: genera título, **precio unitario más bajo**, descripción y tags — ahora con **salida JSON estructurada** (más confiable)
- **Posteo robusto**: detecta los campos por aria-label/placeholder con varios *fallbacks* (ya no depende de contar TABs fijos) y **categoría dinámica**
- **Sesión persistente**: perfil de Chrome guardado → no re-loguear ni pedir 2FA cada vez
- **Anti-baneo**: pausas humanas aleatorias, **límite diario** y espaciado entre publicaciones
- **Historial + logs + reintentos**: registra qué se publicó / qué falló y reintenta automáticamente

## ⚙️ Configuración

Copia `.env.example` a `.env` y complétalo (credenciales y **tu** API key de Gemini):

```bash
cp .env.example .env
```

Variables clave: `FACEBOOK_EMAIL`, `FACEBOOK_PASSWORD`, `GEMINI_API_KEY`,
`MAX_LISTINGS_PER_DAY`, `LISTING_MIN_GAP`/`LISTING_MAX_GAP`, `DEFAULT_CATEGORY`.

> 🔒 Nunca pongas claves en el código. El `.env` está en `.gitignore`.

## 🖥️ Modo escritorio

```bash
pip install -r requirements.txt
python launch_gui.py
```

1. Cargar PDF → 2. Marcar productos → 3. Login Facebook (aprueba 2FA en el celular) → 4. Subir.

## 🌐 Modo web

```bash
# backend
cd web/backend && pip install -r requirements.txt
python main.py                 # http://localhost:8300

# frontend (en otra terminal)
cd web/frontend && npm install && npm run build   # se sirve en / desde el backend
# o en desarrollo:  npm run dev                    # http://localhost:5175
```

Pestañas: **Productos** (subir PDF + análisis IA editable), **Publicar** (config + progreso en vivo por WebSocket), **Historial**.

## 📁 Estructura

```
├── launch_gui.py / marketplace_gui.py   # modo escritorio
├── src/
│   ├── modules/  ai_analyzer · marketplace_automation · facebook_auth
│   │             pdf_extractor · history · human
│   └── config/settings.py
└── web/
    ├── backend/main.py        # FastAPI + WebSocket (reusa /src)
    └── frontend/              # React + Vite (tema oscuro LK)
```

## 📞 Contacto
**SOMOS LK** <3 — WhatsApp: 995665397

---
**Versión**: 3.0 (núcleo robusto + apartado web)
