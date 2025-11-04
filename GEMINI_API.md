# Integración con Gemini AI

## 📘 Información General

Este proyecto utiliza **Google Gemini AI** para el análisis inteligente de imágenes de productos. Gemini es el modelo de IA más avanzado de Google, capaz de entender y analizar contenido multimodal.

## 🔑 API Key Proporcionada

```
API Key: AIzaSyDiyBs75bDIsM7kTl36DT0mccOVFFfETiI
```

**⚠️ Nota de Seguridad**: Esta API key está incluida en el ejemplo. Para uso en producción, obtén tu propia API key en:
https://makersuite.google.com/app/apikey

## 🚀 Modelos Utilizados

### Gemini 2.5 Flash (Análisis de Imágenes)
- **Modelo**: `gemini-2.5-flash`
- **Uso**: Análisis de imágenes de productos
- **Características**:
  - Rápido y eficiente
  - Excelente relación precio-rendimiento
  - Ideal para procesamiento de imágenes a escala
  - Capacidad multimodal (texto + imagen)

### Gemini 2.5 Pro (Chat/Procesamiento Avanzado)
- **Modelo**: `gemini-2.5-pro`
- **Uso**: Procesamiento avanzado y conversacional
- **Características**:
  - Mayor capacidad de razonamiento
  - Mejor para tareas complejas
  - Recomendado para casos de uso premium

## 📊 Capacidades de Análisis

El sistema utiliza Gemini AI para extraer automáticamente:

1. **Título del Producto**
   - Generado automáticamente
   - Máximo 100 caracteres
   - Descriptivo y atractivo

2. **Descripción Detallada**
   - Características principales
   - Condición del producto
   - Detalles relevantes
   - Beneficios para el comprador

3. **Precio Sugerido**
   - Basado en el análisis visual
   - Estimación en dólares
   - Puede ajustarse manualmente

4. **Tags/Etiquetas**
   - 5-10 palabras clave
   - Mejoran la visibilidad
   - Basadas en el contenido de la imagen

## 💡 Cómo Funciona el Análisis

### Proceso de Análisis
```python
# 1. Preparación de imagen
image = prepare_image(image_path)  # Redimensiona si es necesario

# 2. Prompt estructurado a Gemini
prompt = """Analiza esta imagen de un producto y genera:
- TÍTULO: [título descriptivo]
- DESCRIPCIÓN: [descripción detallada]
- PRECIO: [estimación]
- TAGS: [palabras clave]"""

# 3. Envío a Gemini API
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=[prompt, image]
)

# 4. Parsing de respuesta
product_info = parse_response(response.text)
```

### Optimizaciones Implementadas

1. **Redimensionamiento Inteligente**
   - Imágenes grandes se reducen automáticamente
   - Mantiene la relación de aspecto
   - Máximo 2048px por defecto

2. **Múltiples Imágenes**
   - Analiza la primera imagen para info principal
   - Menciona la cantidad total de imágenes
   - Todas las imágenes se suben a Marketplace

3. **Manejo de Errores**
   - Valores por defecto si falla el análisis
   - Reintentos automáticos
   - Logging detallado

## 🎯 Mejores Prácticas

### Para Mejores Resultados

1. **Calidad de Imagen**
   ```
   ✓ Imágenes claras y bien iluminadas
   ✓ Fondo simple y limpio
   ✓ Producto visible desde múltiples ángulos
   ✓ Resolución mínima: 800x600px
   ```

2. **Tipos de Productos**
   - Gemini es especialmente bueno con:
     - Electrónica
     - Ropa y accesorios
     - Muebles
     - Vehículos
     - Productos con texto visible

3. **Formato de PDF**
   - Una imagen por página
   - O múltiples productos en páginas separadas
   - Calidad de exportación: Alta

### Limitaciones a Considerar

1. **Rate Limits**
   - Gemini API tiene límites de uso
   - Para uso intensivo, considera espaciar las solicitudes
   - Monitorea tu cuota en Google AI Studio

2. **Tamaño de Imagen**
   - Máximo recomendado: 2048x2048px
   - Archivos muy grandes se procesan más lento
   - El sistema redimensiona automáticamente

3. **Precisión**
   - La IA hace estimaciones basadas en la imagen
   - Siempre revisa la información generada
   - Ajusta precios según el mercado local

## 🔧 Configuración Avanzada

### Personalizar el Prompt

Edita `src/modules/ai_analyzer.py` para personalizar el prompt:

```python
prompt = """Analiza esta imagen y genera información DETALLADA para Marketplace.

TÍTULO (máx 80 caracteres):
- Debe incluir la marca si es visible
- Menciona la característica principal
- Usa palabras que atraigan compradores

DESCRIPCIÓN (200-500 palabras):
- Estado actual del producto
- Dimensiones si son visibles
- Características técnicas
- Por qué es una buena compra

PRECIO (en USD):
- Basado en la condición visible
- Considera el desgaste
- Rango de precio razonable

TAGS (10 palabras clave):
- Marca, modelo, categoría
- Características principales
- Palabras de búsqueda populares

Responde en este formato exacto:
TÍTULO: [tu respuesta]
DESCRIPCIÓN: [tu respuesta]
PRECIO: [número]
TAGS: [tag1, tag2, ...]"""
```

### Cambiar Modelos

Prueba diferentes modelos según tus necesidades:

```python
# En .env o directamente en el código

# Para velocidad máxima
AI_MODEL_IMAGE=gemini-2.5-flash-lite

# Para balance velocidad/calidad
AI_MODEL_IMAGE=gemini-2.5-flash

# Para máxima calidad
AI_MODEL_IMAGE=gemini-2.5-pro
```

## 📈 Métricas y Monitoreo

### Verificar Uso de API

```python
# Agregar logging en ai_analyzer.py
import logging

logging.info(f"Tokens usados: {response.usage_metadata.total_token_count}")
logging.info(f"Tiempo de respuesta: {response.latency_ms}ms")
```

### Optimizar Costos

1. **Usa Flash en lugar de Pro** cuando sea posible
2. **Reduce el tamaño de imágenes** antes de enviar
3. **Cachea resultados** para productos similares
4. **Procesa en lotes** con delays entre solicitudes

## 🔐 Seguridad de API Key

### Proteger tu API Key

```bash
# 1. Nunca subas .env a Git
echo ".env" >> .gitignore

# 2. Usa variables de entorno en producción
export GEMINI_API_KEY="tu_api_key_aqui"

# 3. Rota keys periódicamente
# Ve a Google AI Studio > API Keys > Revoke
```

### Obtener tu Propia API Key

1. Ve a: https://makersuite.google.com/app/apikey
2. Inicia sesión con tu cuenta Google
3. Click en "Create API Key"
4. Copia la key a tu archivo `.env`

## 🆘 Troubleshooting

### Error: "API key not valid"
```bash
# Verifica que la key esté correcta
grep GEMINI_API_KEY .env

# Prueba la key directamente
curl "https://generativelanguage.googleapis.com/v1/models?key=TU_API_KEY"
```

### Error: "Quota exceeded"
- Espera unos minutos
- Verifica tu cuota en Google AI Studio
- Considera actualizar a un plan de pago

### Error: "Model not found"
- Verifica el nombre del modelo
- Algunos modelos requieren acceso especial
- Usa `gemini-2.5-flash` como fallback

## 📚 Recursos Adicionales

- **Documentación Oficial**: https://ai.google.dev/docs
- **API Reference**: https://ai.google.dev/api
- **Ejemplos**: https://ai.google.dev/examples
- **Comunidad**: https://discuss.ai.google.dev/

## 🎓 Casos de Uso Avanzados

### Análisis por Lotes

```python
# Procesar múltiples PDFs
import glob

pdfs = glob.glob("productos/*.pdf")
for pdf in pdfs:
    print(f"Procesando {pdf}...")
    # Extraer, analizar, publicar
    time.sleep(60)  # Delay entre productos
```

### Análisis Personalizado por Categoría

```python
# En ai_analyzer.py
def analyze_by_category(self, image_path, category):
    if category == "Electronics":
        prompt = "Analiza este dispositivo electrónico..."
    elif category == "Clothing":
        prompt = "Describe esta prenda de ropa..."
    # etc.
```

### Integración con Base de Datos

```python
import sqlite3

# Guardar análisis para referencia futura
conn = sqlite3.connect('products.db')
cursor = conn.cursor()
cursor.execute('''
    INSERT INTO products (title, description, price, tags, analyzed_at)
    VALUES (?, ?, ?, ?, datetime('now'))
''', (info['title'], info['description'], info['price'], 
      ','.join(info['tags'])))
conn.commit()
```

---

**Última actualización**: 2025-01-04
**Versión de Gemini**: 2.5 Flash
**SDK Version**: google-genai 1.0.0
