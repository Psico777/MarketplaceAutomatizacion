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
        # Resize image if too large
        img = Image.open(image_path)
        if max(img.size) > self.max_size:
            img.thumbnail((self.max_size, self.max_size), Image.Resampling.LANCZOS)
            temp_path = image_path.replace('.png', '_resized.png')
            img.save(temp_path)
            return Image.open(temp_path)
        
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
            
            prompt = """Analiza esta imagen de un producto y genera la siguiente información para una publicación en Facebook Marketplace:

1. TÍTULO: Un título descriptivo y atractivo (máximo 100 caracteres)
2. DESCRIPCIÓN: Una descripción detallada del producto, incluyendo:
   - Características principales
   - Condición del producto
   - Detalles relevantes
   - Beneficios
3. PRECIO: Sugiere un precio estimado en dólares (solo el número)
4. TAGS: Lista de 5-10 palabras clave relevantes separadas por comas

Formato de respuesta (importante, usa EXACTAMENTE este formato):
TÍTULO: [tu título aquí]
DESCRIPCIÓN: [tu descripción aquí]
PRECIO: [número sin símbolo de dólar]
TAGS: [tag1, tag2, tag3, tag4, tag5]"""
            
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
                # Extract only numbers
                result['price'] = ''.join(filter(str.isdigit, price_text))
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
