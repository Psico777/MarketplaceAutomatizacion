# 🚀 Facebook Marketplace Automation

Sistema automatizado con interfaz gráfica para subir productos a Facebook Marketplace.

## ⚡ Características

- ✅ **Interfaz Gráfica**: Vista previa de imágenes, selección individual
- ✅ **Análisis IA**: Google Gemini para descripciones automáticas
- ✅ **Super Rápido**: Timeouts optimizados (0.1-0.2s)
- ✅ **Caché Inteligente**: No re-analiza imágenes ya procesadas
- ✅ **Progreso en Tiempo Real**: Barra de progreso y log detallado

## 🚀 Uso Rápido

```bash
# Lanzar GUI
python launch_gui.py
```

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
├── launch_gui.py              # 🚀 Launcher principal
├── marketplace_gui.py         # 🖼️ Interfaz gráfica
├── src/
│   ├── modules/
│   │   ├── ai_analyzer.py           # 🤖 Análisis con IA
│   │   ├── marketplace_automation.py # ⚡ Subida optimizada
│   │   ├── facebook_auth.py         # 🔐 Login 2FA
│   │   └── pdf_extractor.py         # 📄 Extracción PDFs
│   └── config/settings.py     # ⚙️ Configuración
└── ai_analysis_cache.json     # 💾 Caché (auto-generado)
```

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
