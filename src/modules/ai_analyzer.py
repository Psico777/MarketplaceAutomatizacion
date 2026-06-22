"""
AI Image Analyzer Module
Usa Google Gemini para analizar imagenes y generar la info del producto.
Devuelve JSON estructurado (no parseo de texto fragil).
"""
import os
import json
from google import genai
from google.genai import types
from PIL import Image


PROMPT = """Analiza esta imagen de un producto para una publicacion en Facebook Marketplace.

REGLAS DE PRECIO (lee TODOS los precios de la imagen y elige el UNITARIO MAS BAJO):
- Si ves "3 X 50 soles": 50 / 3 = 16.67 -> redondea hacia ARRIBA -> 17.
- Si ves "Por Unidad 20" y "3 X 50": compara 20 vs 17 -> elige 17.
- Si ves "Por Mayor 9.50": usa 9.50 -> redondea -> 9.
- Siempre el precio entero mas bajo posible.

DESCRIPCION (solo ASCII y <3 :) :D, NADA de emojis Unicode), formato:
GENTE LLEGARON LOS [PRODUCTO] AL MEJOR PRECIO <3

:) 1 unidad x [precio unidad] soles
:D 3 unidades a mas x [precio mayor] soles ([precio mayor x 3] soles)

---
(todas las compras por mayor salen a partir de la media docena, puedes variar 6 productos diferentes)
Tambien contamos con precios por docenas, ciento y cajon :)

SOMOS LK <3
Contacto: 995665397 WhatsApp

Responde UNICAMENTE con un objeto JSON valido con esta forma EXACTA:
{
  "title": "nombre del producto, solo texto sin emojis",
  "price": 0,
  "description": "descripcion completa con el formato de arriba, usa \\n para los saltos de linea",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"]
}
- price debe ser un numero entero (el unitario mas bajo).
- tags: minimo 8, relevantes al producto, sin 'remate' ni 'oferta'."""


class AIImageAnalyzer:
    """Analiza imagenes con Gemini y devuelve info de producto estructurada."""

    def __init__(self, api_key, model='gemini-2.5-flash', max_size=2048):
        if not api_key:
            raise ValueError("AIImageAnalyzer requiere una GEMINI_API_KEY valida (ponla en el .env)")
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.max_size = max_size

    def prepare_image(self, image_path):
        """Abre la imagen y la reduce si es muy grande."""
        img = Image.open(image_path)
        if max(img.size) > self.max_size:
            img_copy = img.copy()
            img_copy.thumbnail((self.max_size, self.max_size), Image.Resampling.LANCZOS)
            base, ext = os.path.splitext(image_path)
            temp_path = f"{base}_resized{ext if ext else '.png'}"
            img_copy.save(temp_path)
            return Image.open(temp_path)
        return img

    def analyze_image_for_marketplace(self, image_path):
        """Devuelve dict {title, price, description, tags}."""
        try:
            image = self.prepare_image(image_path)
            response = self.client.models.generate_content(
                model=self.model,
                contents=[PROMPT, image],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.4,
                ),
            )
            data = self._parse_json(response.text)
            return self._normalize(data)
        except Exception as e:
            print(f"Error analizando imagen con IA: {e}")
            return {
                'title': 'Producto en venta',
                'description': 'Producto en excelente condicion. Contactar para mas detalles.',
                'price': '10',
                'tags': ['producto', 'venta', 'marketplace'],
            }

    def _parse_json(self, content):
        """Parsea JSON aunque venga envuelto en ```json ... ```."""
        if not content:
            return {}
        text = content.strip()
        if text.startswith("```"):
            # quitar fences de markdown
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
            text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # ultimo recurso: extraer el primer bloque { ... }
            start, end = text.find('{'), text.rfind('}')
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start:end + 1])
                except json.JSONDecodeError:
                    pass
            return {}

    def _normalize(self, data):
        """Asegura tipos y valores por defecto."""
        title = str(data.get('title') or '').strip() or 'Producto en venta'

        price_raw = data.get('price', 0)
        try:
            price = str(int(float(price_raw)))
        except (TypeError, ValueError):
            import re
            nums = re.findall(r'\d+\.?\d*', str(price_raw))
            price = str(int(float(nums[0]))) if nums else '10'
        if price == '0':
            price = '10'

        description = str(data.get('description') or '').strip() or 'Producto en excelente condicion.'

        tags = data.get('tags') or []
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',') if t.strip()]
        tags = [str(t).strip() for t in tags if str(t).strip()]
        if not tags:
            tags = ['producto', 'venta']

        return {'title': title, 'price': price, 'description': description, 'tags': tags}

    def analyze_single_image(self, image_path):
        return self.analyze_image_for_marketplace(image_path)

    def analyze_multiple_images(self, image_paths):
        if not image_paths:
            return None
        main_result = self.analyze_image_for_marketplace(image_paths[0])
        if len(image_paths) > 1:
            main_result['description'] += f" (Incluye {len(image_paths)} imagenes del producto)"
        return main_result
