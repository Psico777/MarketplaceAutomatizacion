# Guía Detallada de Uso

## 📖 Introducción

Este documento proporciona una guía detallada sobre cómo usar el sistema de automatización de Facebook Marketplace.

## 🎯 Casos de Uso

### 1. Publicar productos desde un PDF

Este es el caso de uso principal del sistema. Sigue estos pasos:

#### Paso 1: Preparar tu PDF
- Crea un PDF con imágenes claras de tu producto
- Las imágenes deben mostrar el producto desde diferentes ángulos
- Asegúrate de que las imágenes sean de buena calidad

#### Paso 2: Configurar credenciales
1. Copia `.env.example` a `.env`
2. Completa tus datos:
```env
FACEBOOK_EMAIL=tu_email@gmail.com
FACEBOOK_PASSWORD=tu_contraseña_segura
GEMINI_API_KEY=AIzaSyDiyBs75bDIsM7kTl36DT0mccOVFFfETiI
```

#### Paso 3: Ejecutar el script
```bash
python main.py create --pdf mi_producto.pdf --category Electronics --condition New
```

#### Paso 4: Supervisar el proceso
El sistema mostrará el progreso:
- ✓ Extracción de imágenes
- ✓ Análisis con IA
- ✓ Login a Facebook
- ✓ Creación de publicación

### 2. Gestionar publicaciones existentes

#### Editar una publicación
```bash
# Cambiar título y precio
python main.py edit \
  --url "https://facebook.com/marketplace/item/123456" \
  --title "Nuevo título del producto" \
  --price "99"

# Cambiar solo la descripción
python main.py edit \
  --url "https://facebook.com/marketplace/item/123456" \
  --description "Nueva descripción detallada del producto"
```

#### Eliminar una publicación
```bash
python main.py delete --url "https://facebook.com/marketplace/item/123456"
```

#### Ver todas tus publicaciones
```bash
python main.py list
```

## 🔐 Configuración Avanzada de 2FA

### Método 1: Usando Google Authenticator

1. **Activar 2FA en Facebook:**
   - Ve a Configuración → Seguridad e inicio de sesión
   - Click en "Usar autenticación de dos factores"
   - Selecciona "App de autenticación"

2. **Obtener el código secreto:**
   - Cuando veas el código QR, haz clic en "¿No puedes escanear el código?"
   - Copia el código de texto (ejemplo: `JBSWY3DPEHPK3PXP`)

3. **Configurar en el sistema:**
   ```env
   FACEBOOK_2FA_SECRET=JBSWY3DPEHPK3PXP
   ```

### Método 2: Entrada manual (sin configurar)

Si no configuras `FACEBOOK_2FA_SECRET`, el sistema pausará 60 segundos para que ingreses el código manualmente cuando Facebook lo solicite.

## 🎨 Personalización del Análisis de IA

El sistema usa Gemini AI para analizar imágenes. Puedes personalizar el comportamiento:

### Cambiar el modelo
En `.env`:
```env
# Para análisis más rápido (recomendado)
AI_MODEL_IMAGE=gemini-2.5-flash

# Para análisis más detallado
AI_MODEL_IMAGE=gemini-2.5-pro
```

### Ajustar el tamaño de imagen
```env
# Tamaño máximo de imagen en píxeles (reduce para procesar más rápido)
MAX_IMAGE_SIZE=2048
```

## 🔧 Configuración del Navegador

### Modo sin interfaz (Headless)
Para ejecutar sin ver el navegador:
```env
HEADLESS=True
```

### Ajustar tiempos de espera
Si tienes una conexión lenta, aumenta el tiempo:
```env
IMPLICIT_WAIT=15  # Espera 15 segundos en lugar de 10
```

## 📝 Ejemplos de Código

### Uso programático

Puedes usar los módulos directamente en tu código Python:

```python
from src.config.settings import Config
from src.modules.pdf_extractor import PDFImageExtractor
from src.modules.ai_analyzer import AIImageAnalyzer
from src.modules.facebook_auth import FacebookAuthenticator
from src.modules.marketplace_automation import MarketplaceAutomation

# Extraer imágenes
extractor = PDFImageExtractor(Config.TEMP_DIR)
images = extractor.extract_images_from_pdf("producto.pdf")

# Analizar con IA
analyzer = AIImageAnalyzer(
    api_key=Config.GEMINI_API_KEY,
    model=Config.AI_MODEL_IMAGE
)
info = analyzer.analyze_multiple_images(images)

print(f"Título: {info['title']}")
print(f"Precio: ${info['price']}")
print(f"Descripción: {info['description']}")

# Autenticar
auth = FacebookAuthenticator(
    email=Config.FACEBOOK_EMAIL,
    password=Config.FACEBOOK_PASSWORD,
    two_fa_secret=Config.FACEBOOK_2FA_SECRET
)

if auth.login():
    # Crear publicación
    marketplace = MarketplaceAutomation(auth.driver)
    success = marketplace.create_listing(
        title=info['title'],
        description=info['description'],
        price=info['price'],
        category="Electronics",
        condition="New",
        images=images
    )
    
auth.close()
```

## 🚨 Solución de Problemas Comunes

### Error: "Failed to login"

**Posibles causas:**
1. Credenciales incorrectas
2. Facebook requiere verificación
3. Conexión lenta

**Soluciones:**
```bash
# 1. Verifica las credenciales en .env
cat .env | grep FACEBOOK_

# 2. Desactiva headless para ver qué pasa
# En .env: HEADLESS=False

# 3. Aumenta el tiempo de espera
# En .env: IMPLICIT_WAIT=20
```

### Error: "Chrome driver not found"

```bash
# Actualizar webdriver-manager
pip install --upgrade webdriver-manager

# Si persiste, instala Chrome manualmente
# Ubuntu/Debian:
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb
```

### Error: "Failed to analyze image"

**Posibles causas:**
1. API Key de Gemini inválida
2. Imagen muy grande
3. Límite de API alcanzado

**Soluciones:**
```bash
# 1. Verifica tu API Key
# Ve a: https://makersuite.google.com/app/apikey

# 2. Reduce el tamaño máximo de imagen
# En .env: MAX_IMAGE_SIZE=1024

# 3. Espera unos minutos si alcanzaste el límite
```

### Error: "Failed to upload images"

**Causas comunes:**
1. Imágenes no existen
2. Formato de imagen no soportado
3. Imágenes muy pesadas

**Soluciones:**
```python
# Verifica que las imágenes existen
import os
for img in image_paths:
    print(f"{img}: {os.path.exists(img)}")

# Formatos soportados: PNG, JPG, JPEG
# Tamaño máximo: ~10MB por imagen
```

## 📊 Mejores Prácticas

### 1. Calidad de las imágenes
- Usa imágenes claras y bien iluminadas
- Incluye múltiples ángulos del producto
- Resolución mínima: 800x600 píxeles

### 2. Información del producto
- El AI es más preciso con productos claramente visibles
- Incluye texto visible en la imagen si es relevante
- Evita fondos desordenados

### 3. Uso responsable
- No publiques más de 5 productos por hora
- Espera al menos 1 minuto entre publicaciones
- Facebook puede detectar comportamiento automatizado

### 4. Seguridad
- Nunca compartas tu archivo `.env`
- Usa contraseñas fuertes
- Activa 2FA en Facebook
- Cambia tu API key si la expones accidentalmente

## 🔄 Flujo Completo Recomendado

```bash
# 1. Preparar el entorno
cp .env.example .env
nano .env  # Edita con tus credenciales

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Crear PDF con imágenes del producto
# (usa cualquier herramienta para crear el PDF)

# 4. Ejecutar primera vez (sin headless para supervisar)
python main.py create --pdf producto.pdf --category Electronics --condition New

# 5. Si todo funciona, puedes usar headless
# En .env: HEADLESS=True

# 6. Automatizar para múltiples productos
for pdf in productos/*.pdf; do
    python main.py create --pdf "$pdf" --category Electronics
    sleep 300  # Espera 5 minutos entre cada uno
done
```

## 🎓 Recursos Adicionales

### APIs Utilizadas
- **Gemini AI**: https://ai.google.dev/
- **Selenium**: https://selenium-python.readthedocs.io/

### Comunidad
- Reporta problemas: GitHub Issues
- Contribuciones: Pull Requests bienvenidos

### Actualizaciones
El sistema se actualiza regularmente para adaptarse a cambios en Facebook y mejorar la precisión de la IA.

```bash
# Actualizar a la última versión
git pull origin main
pip install -r requirements.txt --upgrade
```

## 💡 Tips Avanzados

### Procesar PDFs grandes
```python
# Para PDFs con muchas páginas, procesar de a una
from src.modules.pdf_extractor import PDFImageExtractor

extractor = PDFImageExtractor()
info = extractor.get_pdf_info("producto_grande.pdf")
print(f"El PDF tiene {info['num_pages']} páginas")

# Procesa las primeras 3 páginas solamente
# (edita pdf_extractor.py para agregar parámetro de páginas)
```

### Usar proxies
Si necesitas usar un proxy:
```python
# En facebook_auth.py, agrega:
chrome_options.add_argument('--proxy-server=http://proxy:port')
```

### Logs detallados
Activa logs para debugging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

**Última actualización**: 2025-01-04
**Versión**: 1.0.0
