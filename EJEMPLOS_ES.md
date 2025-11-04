# Ejemplos de Uso en Español

## 🎯 Casos de Uso Reales

### Ejemplo 1: Vender un Teléfono Móvil

```bash
# 1. Crea un PDF con fotos del teléfono desde diferentes ángulos
# 2. Ejecuta el comando:

python main.py create \
  --pdf mi_telefono.pdf \
  --category Electronics \
  --condition Used \
  --location "Madrid, España"
```

**Resultado esperado:**
- **Título**: "iPhone 12 Pro 128GB Azul Pacífico"
- **Precio**: $450
- **Descripción**: "iPhone 12 Pro en excelente estado, 128GB de almacenamiento..."
- **Tags**: iPhone, Apple, smartphone, teléfono, móvil, iOS

### Ejemplo 2: Vender Muebles

```bash
python main.py create \
  --pdf sofa_vintage.pdf \
  --category Furniture \
  --condition Good \
  --location "Barcelona, España"
```

**Resultado esperado:**
- **Título**: "Sofá Vintage de Cuero Marrón 3 Plazas"
- **Precio**: $200
- **Descripción**: "Sofá vintage en cuero genuino, cómodo y elegante..."
- **Tags**: sofá, vintage, cuero, mueble, sala, living

### Ejemplo 3: Vender Ropa

```bash
python main.py create \
  --pdf chaqueta_nike.pdf \
  --category Clothing \
  --condition New \
  --location "Ciudad de México"
```

### Ejemplo 4: Vender Videojuegos

```bash
python main.py create \
  --pdf juegos_ps5.pdf \
  --category Gaming \
  --condition Like New \
  --location "Buenos Aires, Argentina"
```

## 🔄 Gestión de Publicaciones

### Actualizar Precio de una Publicación

```bash
# Bajé el precio de mi producto
python main.py edit \
  --url "https://facebook.com/marketplace/item/123456789" \
  --price "350"
```

### Actualizar Título y Descripción

```bash
python main.py edit \
  --url "https://facebook.com/marketplace/item/123456789" \
  --title "¡REBAJADO! iPhone 12 Pro 128GB" \
  --description "Precio rebajado por venta rápida. Incluye cargador original y funda."
```

### Ver Todas tus Publicaciones

```bash
python main.py list
```

**Salida:**
```
Encontradas 5 publicaciones:
1. https://facebook.com/marketplace/item/111111
2. https://facebook.com/marketplace/item/222222
3. https://facebook.com/marketplace/item/333333
...
```

### Eliminar una Publicación

```bash
# Producto vendido, eliminar del marketplace
python main.py delete \
  --url "https://facebook.com/marketplace/item/123456789"
```

## 🛠️ Flujos de Trabajo Completos

### Flujo 1: Limpieza de Casa

Estás haciendo limpieza y quieres vender varios artículos:

```bash
# Paso 1: Prepara PDFs con fotos
# - old_furniture.pdf (sofá, mesa, sillas)
# - electronics.pdf (laptop vieja, monitor)
# - books.pdf (colección de libros)

# Paso 2: Publica cada categoría
python main.py create --pdf old_furniture.pdf --category Furniture
sleep 300  # Espera 5 minutos

python main.py create --pdf electronics.pdf --category Electronics
sleep 300

python main.py create --pdf books.pdf --category Books
```

### Flujo 2: Tienda Online

Tienes una pequeña tienda y quieres automatizar publicaciones:

```bash
#!/bin/bash
# script_publicar_inventario.sh

# Array de productos
productos=(
    "producto1.pdf:Electronics:New"
    "producto2.pdf:Clothing:New"
    "producto3.pdf:Toys:New"
)

# Publicar cada producto
for item in "${productos[@]}"; do
    IFS=':' read -r pdf category condition <<< "$item"
    
    echo "Publicando $pdf..."
    python main.py create \
        --pdf "inventario/$pdf" \
        --category "$category" \
        --condition "$condition" \
        --location "Tu Ciudad"
    
    echo "Esperando 5 minutos antes del siguiente..."
    sleep 300
done

echo "¡Todos los productos publicados!"
```

### Flujo 3: Actualización Masiva de Precios

Quieres bajar precios de productos que no se venden:

```python
# script_actualizar_precios.py
import subprocess
import time

# URLs de tus publicaciones y nuevos precios
productos = [
    ("https://facebook.com/marketplace/item/111", "100"),
    ("https://facebook.com/marketplace/item/222", "75"),
    ("https://facebook.com/marketplace/item/333", "50"),
]

for url, nuevo_precio in productos:
    print(f"Actualizando {url} a ${nuevo_precio}...")
    
    subprocess.run([
        "python", "main.py", "edit",
        "--url", url,
        "--price", nuevo_precio
    ])
    
    print("Esperando 2 minutos...")
    time.sleep(120)

print("¡Precios actualizados!")
```

## 📝 Tips y Trucos

### Crear PDFs con Fotos del Móvil

**Opción 1: Usando Google Drive**
1. Sube fotos a Google Drive
2. Selecciónalas todas
3. Click derecho → Abrir con → Google Docs
4. Archivo → Descargar → PDF

**Opción 2: Usando apps**
- **Android**: Cam Scanner, Adobe Scan
- **iOS**: Notas (escanear documentos)

### Organización de Productos

```
productos/
├── electronica/
│   ├── telefono_1.pdf
│   ├── laptop_1.pdf
│   └── auriculares_1.pdf
├── ropa/
│   ├── chaqueta_nike.pdf
│   └── zapatillas_adidas.pdf
└── muebles/
    ├── sofa_vintage.pdf
    └── mesa_comedor.pdf
```

### Script para Procesar Carpeta Completa

```python
# publicar_carpeta.py
import os
import sys
import subprocess
import time

carpeta = sys.argv[1] if len(sys.argv) > 1 else "productos"

# Obtener todos los PDFs
pdfs = []
for root, dirs, files in os.walk(carpeta):
    for file in files:
        if file.endswith('.pdf'):
            pdfs.append(os.path.join(root, file))

print(f"Encontrados {len(pdfs)} PDFs para publicar")

# Publicar cada uno
for i, pdf in enumerate(pdfs, 1):
    print(f"\n[{i}/{len(pdfs)}] Publicando {pdf}...")
    
    subprocess.run([
        "python", "main.py", "create",
        "--pdf", pdf,
        "--category", "Other"
    ])
    
    if i < len(pdfs):
        print("Esperando 5 minutos antes del siguiente...")
        time.sleep(300)

print("\n¡Proceso completado!")
```

**Uso:**
```bash
python publicar_carpeta.py productos/electronica
```

## 🎨 Personalización del Análisis de IA

### Modificar el Prompt para tu Idioma

Si quieres que las descripciones sean en un estilo específico, edita `src/modules/ai_analyzer.py`:

```python
prompt = """Analiza esta imagen de un producto para venta en Argentina.

TÍTULO (80 caracteres máximo):
- Usa términos populares en Argentina
- Incluye la marca prominentemente
- Que sea llamativo

DESCRIPCIÓN (estilo argentino):
- Usá voseo (ej: "tenés", "podés")
- Mencioná si hacés envíos
- Estado del producto en detalle
- Forma de pago que aceptás

PRECIO (en pesos argentinos):
- Precio justo según el mercado local
- Considerá el estado

TAGS (palabras que busca la gente):
- Incluí variaciones del nombre
- Marcas y modelos
- Características clave

Formato:
TÍTULO: [tu título]
DESCRIPCIÓN: [descripción localizada]
PRECIO: [solo número]
TAGS: [tag1, tag2, tag3]"""
```

### Análisis Especializado por Categoría

```python
# En ai_analyzer.py, agrega:

def analyze_electronics(self, image_path):
    """Análisis especializado para electrónica"""
    prompt = """Analiza este dispositivo electrónico con detalle técnico:
    - Marca y modelo exacto si es visible
    - Estado de la pantalla/carcasa
    - Accesorios incluidos visibles
    - Especificaciones técnicas aparentes"""
    # ... resto del código

def analyze_clothing(self, image_path):
    """Análisis especializado para ropa"""
    prompt = """Analiza esta prenda de ropa:
    - Talla visible en etiquetas
    - Marca y diseño
    - Estado de la tela
    - Estilo (casual, formal, deportivo)"""
    # ... resto del código
```

## 🔍 Debugging y Solución de Problemas

### Ver lo que está haciendo el navegador

```bash
# Desactiva el modo headless en .env
HEADLESS=False

# Ejecuta el script y observa
python main.py create --pdf producto.pdf
```

### Guardar Screenshots Automáticos

Agrega en `facebook_auth.py`:

```python
# Después de cada paso importante
self.driver.save_screenshot(f'screenshots/step_{paso}.png')
```

### Logging Detallado

```python
# En main.py, agrega al inicio:
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='marketplace_automation.log'
)
```

## 🌟 Casos de Éxito

### Historia 1: Vendedor de Tecnología
"Vendía celulares usados. Antes tardaba 30 minutos en publicar cada uno. Ahora proceso 20 teléfonos en una mañana."

### Historia 2: Tienda de Ropa Vintage
"Tengo fotos de 100+ prendas. El sistema me genera descripciones únicas para cada una en minutos."

### Historia 3: Mudanza Internacional
"Necesitaba vender todo antes de mudarme. Publiqué 50 artículos en un día."

## 📞 Soporte y Comunidad

¿Tienes dudas o necesitas ayuda?

1. **Revisa la documentación**:
   - README.md
   - USAGE_GUIDE.md
   - GEMINI_API.md

2. **Abre un issue en GitHub**:
   - Describe tu problema
   - Incluye logs de error
   - Menciona tu sistema operativo

3. **Contribuye al proyecto**:
   - Comparte tus mejoras
   - Reporta bugs
   - Sugiere nuevas funciones

---

**Recuerda**: Usa el sistema responsablemente y respeta los términos de servicio de Facebook.

*¡Éxitos en tus ventas! 🚀*
