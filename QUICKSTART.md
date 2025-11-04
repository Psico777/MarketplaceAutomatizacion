# 🚀 Quick Start Guide

## Inicio Rápido en 5 Minutos

### 1. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar Credenciales
```bash
cp .env.example .env
nano .env  # Edita con tus datos
```

Mínimo requerido en `.env`:
```env
FACEBOOK_EMAIL=tu_email@gmail.com
FACEBOOK_PASSWORD=tu_contraseña
GEMINI_API_KEY=AIzaSyDiyBs75bDIsM7kTl36DT0mccOVFFfETiI
```

### 3. Verificar Instalación
```bash
python test_setup.py
```

### 4. Crear tu Primera Publicación
```bash
python main.py create --pdf mi_producto.pdf
```

## 📋 Comandos Principales

| Acción | Comando |
|--------|---------|
| **Crear publicación** | `python main.py create --pdf producto.pdf` |
| **Editar publicación** | `python main.py edit --url URL --title "Nuevo título"` |
| **Eliminar publicación** | `python main.py delete --url URL` |
| **Ver tus publicaciones** | `python main.py list` |

## 🎯 Casos de Uso

```bash
# Vender electrónica
python main.py create --pdf telefono.pdf --category Electronics --condition Used

# Vender ropa
python main.py create --pdf chaqueta.pdf --category Clothing --condition New

# Vender muebles
python main.py create --pdf sofa.pdf --category Furniture --condition Good

# Actualizar precio
python main.py edit --url "facebook.com/marketplace/item/123" --price "99"
```

## 🛠️ Estructura del Proyecto

```
MarketplaceAutomatizacion/
├── main.py                 # Script principal
├── examples.py             # Ejemplos de código
├── test_setup.py          # Verificar instalación
├── requirements.txt       # Dependencias
├── .env                   # Configuración (crear desde .env.example)
├── README.md             # Documentación principal
├── USAGE_GUIDE.md        # Guía detallada
├── EJEMPLOS_ES.md        # Ejemplos en español
├── GEMINI_API.md         # Info sobre Gemini AI
└── src/
    ├── config/
    │   └── settings.py   # Configuración
    └── modules/
        ├── pdf_extractor.py        # PDF → Imágenes
        ├── ai_analyzer.py          # Análisis IA
        ├── facebook_auth.py        # Login Facebook
        └── marketplace_automation.py # Automatización
```

## 🔑 Variables de Entorno

### Esenciales
- `FACEBOOK_EMAIL` - Tu email de Facebook
- `FACEBOOK_PASSWORD` - Tu contraseña
- `GEMINI_API_KEY` - API key de Gemini AI

### Opcionales
- `FACEBOOK_2FA_SECRET` - Para autenticación 2FA
- `HEADLESS=False` - Ver el navegador
- `IMPLICIT_WAIT=10` - Tiempo de espera

## 🆘 Solución Rápida de Problemas

### "Module not found"
```bash
pip install -r requirements.txt
```

### "Login failed"
```bash
# Verifica credenciales
cat .env | grep FACEBOOK_

# Desactiva headless para ver el problema
# En .env: HEADLESS=False
```

### "Chrome driver not found"
```bash
pip install --upgrade webdriver-manager
```

### "API key invalid"
- Verifica tu API key en: https://makersuite.google.com/app/apikey
- La API key incluida en el ejemplo debería funcionar

## 📚 Documentación Completa

- **README.md** - Vista general del proyecto
- **USAGE_GUIDE.md** - Guía detallada de uso
- **EJEMPLOS_ES.md** - Casos de uso en español
- **GEMINI_API.md** - Información sobre Gemini AI

## 💡 Tips Rápidos

1. **Primeras pruebas**: Desactiva `HEADLESS` para ver qué pasa
2. **PDFs de calidad**: Usa imágenes claras y bien iluminadas
3. **Espera entre publicaciones**: 5 minutos mínimo
4. **Revisa el resultado**: La IA genera sugerencias, siempre revisa antes de publicar

## 🎓 Aprende Más

### Ejemplos Interactivos
```bash
python examples.py
```

Opciones:
1. Workflow completo PDF → Marketplace
2. Editar publicación existente
3. Listar tus publicaciones

### Uso Programático

```python
from src.config.settings import Config
from src.modules.ai_analyzer import AIImageAnalyzer

# Analizar imagen
analyzer = AIImageAnalyzer(
    api_key=Config.GEMINI_API_KEY,
    model='gemini-2.5-flash'
)

info = analyzer.analyze_image_for_marketplace('producto.jpg')
print(f"Título: {info['title']}")
print(f"Precio: ${info['price']}")
```

## ⚡ Automatización Avanzada

### Script para Múltiples Productos

```bash
#!/bin/bash
for pdf in productos/*.pdf; do
    python main.py create --pdf "$pdf"
    sleep 300  # 5 minutos entre cada uno
done
```

### Actualización Masiva

```python
# Script Python para actualizar varios productos
import subprocess

productos = [
    ("url1", "100"),
    ("url2", "150"),
]

for url, precio in productos:
    subprocess.run(["python", "main.py", "edit", "--url", url, "--price", precio])
```

## 🌟 Características Destacadas

✅ **Análisis IA Automático** - Gemini AI genera títulos, descripciones y precios
✅ **Soporte 2FA** - Autenticación de dos factores completamente automatizada
✅ **Sin APIs de Facebook** - Usa Selenium para evitar permisos complejos
✅ **Multiidioma** - Documentación completa en español
✅ **Fácil de Usar** - CLI simple e intuitivo

## 🎯 Próximos Pasos

1. ✅ Verificar instalación con `python test_setup.py`
2. ✅ Crear tu primer PDF con fotos de producto
3. ✅ Ejecutar `python main.py create --pdf producto.pdf`
4. ✅ Ver el resultado en Facebook Marketplace
5. ✅ Explorar funciones avanzadas en USAGE_GUIDE.md

## 📞 Necesitas Ayuda?

- **Documentación**: Lee los archivos .md en el proyecto
- **Issues**: Reporta problemas en GitHub
- **Contribuir**: Pull requests bienvenidos

---

**¡Listo para empezar! 🎉**

```bash
python main.py create --pdf tu_producto.pdf
```
