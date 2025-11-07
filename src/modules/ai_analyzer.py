"""
AI Image Analyzer Module
Uses Google Gemini AI to analyze images and generate product descriptions
"""
import base64
import os
from google import genai
from google.genai import types
from PIL import Image


class AIImageAnalyzer:
    """Analyze images using Gemini AI to generate product information"""
    
    def __init__(self, api_key, model='gemini-2.5-flash', max_size=2048):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.max_size = max_size
    
    def prepare_image(self, image_path):
        """
        Prepare image for Gemini AI processing
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            PIL.Image: Prepared image
        """
        # Open and check if resize is needed
        img = Image.open(image_path)
        if max(img.size) > self.max_size:
            # Create a copy and resize
            img_copy = img.copy()
            img_copy.thumbnail((self.max_size, self.max_size), Image.Resampling.LANCZOS)
            
            # Get file extension and create temp path
            import os
            base, ext = os.path.splitext(image_path)
            temp_path = f"{base}_resized{ext if ext else '.png'}"
            
            img_copy.save(temp_path)
            return Image.open(temp_path)
        
        # Return the original image if no resize needed
        return img
    
    def analyze_image_for_marketplace(self, image_path):
        """
        Analyze an image and generate marketplace listing information
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            dict: Dictionary containing title, description, price, tags
        """
        try:
            # Prepare the image
            image = self.prepare_image(image_path)
            
            prompt = """Analiza esta imagen de un producto/juguete para una publicación en Facebook Marketplace.

INSTRUCCIONES CRÍTICAS - LEE LA IMAGEN CON ATENCIÓN:

1. TÍTULO: 
   - Copia EXACTAMENTE el nombre del producto que aparece en la imagen
   - NO USES EMOJIS - Solo texto simple

2. PRECIO (MUY IMPORTANTE - LEE CON CUIDADO):
   - Busca en la imagen TODOS los precios que aparecen
   - Debes calcular el PRECIO UNITARIO MÁS BAJO:
   
   CASO 1: Si ves "3 X 50 soles" (o similar):
   - Divide: 50 ÷ 3 = 16.67
   - Redondea hacia ARRIBA: 17 soles
   - PRECIO: 17
   
   CASO 2: Si ves "Por Unidad 20.00" y "3 X 50 soles":
   - Calcula: 50 ÷ 3 = 16.67 → 17 soles
   - Compara: 20 vs 17
   - El MÁS BAJO es 17
   - PRECIO: 17
   
   CASO 3: Si ves "Por Unidad 14.00" y "Por Mayor 9.50":
   - Ya te dan el precio por mayor directo: 9.50
   - Redondea: 9 soles
   - PRECIO: 9
   
   REGLA: Siempre escoge el precio unitario más bajo (ya sea dividiendo o si ya te lo dan)

3. DESCRIPCIÓN:
   - Analiza TODOS los precios que aparecen en la imagen
   - USA saltos de línea (\n) para separar secciones
   - NO uses emojis Unicode - SOLO ASCII: <3 :) :D
   - Formato EXACTO:

GENTE LLEGARON LOS [NOMBRE DEL PRODUCTO] AL MEJOR PRECIO <3

[SI VES PRECIO "Por Unidad" EN LA IMAGEN:]
:) 1 unidad x [ese precio] soles

[SI VES PRECIO "Por Mayor" EN LA IMAGEN:]
:D 3 unidades a mas x [ese precio] soles ([ese precio x 3] soles)

---
(todas las compras por mayor salen a partir de la media docena puedes variar 6 productos diferentes)

Tambien contamos con precios por docenas, ciento y cajon :)

SOMOS LK <3

Contacto: 995665397 WhatsApp

EJEMPLOS CORRECTOS:
- Si ves "Por Unidad 14.00" y "Por Mayor 9.50":
  PRECIO: 9 (ya te dan el precio por mayor directo)
  Descripción incluye:
  1 unidad x 14 soles
  3 unidades a mas x 9 soles (27 soles)

- Si ves "por unidad 20.00" y "Por mayor 3 X 50 soles":
  PRECIO: 17 (50 ÷ 3 = 16.67 → 17, que es menor que 20)
  Descripción incluye:
  1 unidad x 20 soles
  3 unidades a mas x 17 soles (51 soles)

- Si ves "por unidad 14.00" y "3 X 24 soles":
  PRECIO: 8 (24 ÷ 3 = 8, que es menor que 14)
  Descripción incluye:
  1 unidad x 14 soles
  3 unidades a mas x 8 soles (24 soles)

4. TAGS: Mínimo 8 palabras clave relevantes al producto/juguete (NO incluir 'remate' ni 'oferta')

Formato de respuesta (usa EXACTAMENTE este formato):
TÍTULO: [nombre producto de la imagen - SOLO TEXTO, SIN EMOJIS]
PRECIO: [precio por mayor - el MÁS BAJO - redondeado a entero]
DESCRIPCIÓN: [descripción corta + formato completo con precios REALES de la imagen, solo texto ASCII y <3]
TAGS: [tag1, tag2, tag3, tag4, tag5, tag6, tag7, tag8]"""
            
            # Generate content with Gemini
            response = self.client.models.generate_content(
                model=self.model,
                contents=[prompt, image]
            )
            
            # Parse the response
            content = response.text
            result = self._parse_ai_response(content)
            
            print(f"AI Analysis completed for {image_path}")
            return result
            
        except Exception as e:
            print(f"Error analyzing image with AI: {e}")
            # Return default values in case of error
            return {
                'title': 'Producto en venta',
                'description': 'Producto en excelente condición. Contactar para más detalles.',
                'price': '0',
                'tags': ['producto', 'venta', 'marketplace']
            }
    
    def _parse_ai_response(self, content):
        """
        Parse AI response into structured data
        
        Args:
            content (str): Raw AI response
            
        Returns:
            dict: Parsed product information
        """
        result = {
            'title': '',
            'description': '',
            'price': '0',
            'tags': []
        }
        
        lines = content.split('\n')
        current_field = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('TÍTULO:'):
                result['title'] = line.replace('TÍTULO:', '').strip()
                current_field = 'title'
            elif line.startswith('DESCRIPCIÓN:'):
                result['description'] = line.replace('DESCRIPCIÓN:', '').strip()
                current_field = 'description'
            elif line.startswith('PRECIO:'):
                price_text = line.replace('PRECIO:', '').strip()
                # Extract only digits and round to integer
                # Remove any decimals, keep only whole numbers
                import re
                # Find first number in the text (could be "9.50" or "20.00" or just "9")
                numbers = re.findall(r'\d+\.?\d*', price_text)
                if numbers:
                    # Convert to float then to int to round down
                    result['price'] = str(int(float(numbers[0])))
                else:
                    result['price'] = '0'
                current_field = 'price'
            elif line.startswith('TAGS:'):
                tags_text = line.replace('TAGS:', '').strip()
                result['tags'] = [tag.strip() for tag in tags_text.split(',')]
                current_field = 'tags'
            elif current_field == 'description' and line:
                # Continue multi-line description
                result['description'] += ' ' + line
        
        # Ensure we have valid data
        if not result['title']:
            result['title'] = 'Producto en venta'
        if not result['description']:
            result['description'] = 'Producto en excelente condición.'
        if not result['price'] or result['price'] == '0':
            result['price'] = '10'
        if not result['tags']:
            result['tags'] = ['producto', 'venta']
        
        return result
    
    def analyze_single_image(self, image_path):
        """
        Analyze a single image (alias for analyze_image_for_marketplace)
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            dict: Product information
        """
        return self.analyze_image_for_marketplace(image_path)
    
    def analyze_multiple_images(self, image_paths):
        """
        Analyze multiple images and combine the information
        
        Args:
            image_paths (list): List of image paths
            
        Returns:
            dict: Combined product information
        """
        if not image_paths:
            return None
        
        # Analyze first image for main information
        main_result = self.analyze_image_for_marketplace(image_paths[0])
        
        # If multiple images, mention it in description
        if len(image_paths) > 1:
            main_result['description'] += f" (Incluye {len(image_paths)} imágenes del producto)"
        
        return main_result
