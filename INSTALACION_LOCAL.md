# 📥 Instalación en tu Laptop (Windows/Mac/Linux)

## ✅ Actualizaciones Recientes

- ✨ Mejoras en ChromeDriver para evitar errores de descarga
- 🔐 Mejor manejo de autenticación 2FA con instrucciones claras
- 📄 PDF de prueba incluido (`product_test.pdf`)
- 📸 Capturas de pantalla automáticas para debugging
- 🎨 Modo no-headless por defecto para ver el navegador

---

## 🚀 Pasos de Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/Psico777/MarketplaceAutomatizacion.git
cd MarketplaceAutomatizacion
```

### 2. Instalar Python (si no lo tienes)

- **Windows**: Descarga desde [python.org](https://www.python.org/downloads/)
- **Mac**: `brew install python3`
- **Linux**: `sudo apt-get install python3 python3-pip`

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Instalar Google Chrome

Asegúrate de tener Google Chrome instalado en tu sistema.

### 5. Crear archivo `.env` con tus credenciales

Crea un archivo llamado `.env` en la raíz del proyecto con este contenido:

```bash
# Facebook Credentials
FACEBOOK_EMAIL=995665397
FACEBOOK_PASSWORD=+51995665397

# 2FA Settings (opcional - solo si tienes 2FA activado)
# Si tienes 2FA, agrega tu código secreto aquí
# FACEBOOK_2FA_SECRET=tu_codigo_secreto_2fa

# Gemini API Key (ya está configurada una de demo)
GEMINI_API_KEY=AIzaSyDiyBs75bDIsM7kTl36DT0mccOVFFfETiI

# Browser Settings
# En tu laptop local, usa False para VER el navegador
HEADLESS=False
IMPLICIT_WAIT=10

# Image Analysis Settings
AI_MODEL_IMAGE=gemini-2.5-flash
AI_MODEL_CHAT=gemini-2.5-pro
MAX_IMAGE_SIZE=2048
```

### 6. Verificar instalación

```bash
python test_setup.py
```

Deberías ver todos los checks en ✓ (verde).

---

## 🎯 Uso Básico

### Crear una publicación desde un PDF

```bash
python main.py create --pdf product_test.pdf --category "Electronics" --condition "Used"
```

### Usar tu propio PDF

```bash
python main.py create --pdf ruta/a/tu/producto.pdf --category "Electronics" --condition "New"
```

### Ver todas las opciones

```bash
python main.py --help
```

---

## 🔐 Sobre la Autenticación 2FA

### Opción 1: Sin código secreto 2FA
Si NO tienes el código secreto 2FA configurado en el `.env`, el programa:
1. Abrirá el navegador
2. Iniciará sesión
3. Te pedirá que ingreses el código 2FA manualmente en el navegador
4. Esperará 60 segundos para que lo ingreses

### Opción 2: Con código secreto 2FA
Si TIENES el código secreto 2FA y lo configuras en `FACEBOOK_2FA_SECRET`, el programa ingresará el código automáticamente.

**¿Cómo obtener el código secreto 2FA?**
- Ve a Configuración de Facebook > Seguridad > Autenticación de dos factores
- Configura o reconfigura tu autenticador
- Cuando te muestre el código QR, busca la opción "¿No puedes escanear?" o similar
- Te mostrará un código alfanumérico largo - ese es tu código secreto

---

## 📝 Comandos Disponibles

### Crear publicación
```bash
python main.py create --pdf producto.pdf --category "Electronics" --condition "New" --location "Lima"
```

### Listar tus publicaciones
```bash
python main.py list
```

### Editar publicación
```bash
python main.py edit --url "URL_DE_PUBLICACION" --title "Nuevo Título" --price "500"
```

### Eliminar publicación
```bash
python main.py delete --url "URL_DE_PUBLICACION"
```

---

## 🐛 Solución de Problemas

### Error: Chrome no se abre
- Asegúrate de tener Google Chrome instalado
- Intenta actualizar Chrome a la última versión

### Error: 2FA falla
- Si tienes 2FA activado, asegúrate de tener el código secreto correcto en `.env`
- O deja el campo vacío e ingresa el código manualmente cuando se abra el navegador

### Error: No se extraen imágenes del PDF
- Verifica que el PDF tenga imágenes reales (no solo texto)
- Asegúrate de que `poppler` esté instalado:
  - **Windows**: Descarga desde [poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases/)
  - **Mac**: `brew install poppler`
  - **Linux**: `sudo apt-get install poppler-utils`

### Error: API Key de Gemini
- La clave de demo incluida puede tener límites de uso
- Obtén tu propia clave gratis en: https://makersuite.google.com/app/apikey

---

## 📸 Capturas de Pantalla

El programa ahora guarda capturas de pantalla en la carpeta `screenshots/` para ayudarte a debug:
- `after_login.png` - Después del intento de login
- `login_failed.png` - Si el login falla

---

## ⚠️ ADVERTENCIA LEGAL

Este software es para **PROPÓSITOS EDUCATIVOS Y DE DEMOSTRACIÓN** únicamente.

El uso de herramientas de automatización con Facebook puede **VIOLAR sus Términos de Servicio**. 
- Tu cuenta puede ser suspendida o terminada
- Los autores NO son responsables de ninguna consecuencia

Lee los [Términos de Servicio de Facebook](https://www.facebook.com/terms.php) antes de usar.

---

## 💡 Tips

1. **Primera vez**: Ejecuta con `HEADLESS=False` para ver qué hace el navegador
2. **Producción**: Una vez que funcione, cambia a `HEADLESS=True` para mayor velocidad
3. **PDFs**: Usa PDFs con imágenes claras y de buena calidad para mejor análisis de IA
4. **Frecuencia**: No ejecutes el script muchas veces seguidas - Facebook podría detectarlo

---

## 📞 Soporte

Si tienes problemas:
1. Verifica que seguiste todos los pasos de instalación
2. Revisa las capturas de pantalla en `screenshots/`
3. Ejecuta `python test_setup.py` para verificar la configuración
4. Crea un issue en GitHub con los detalles del error

---

¡Buena suerte! 🚀
