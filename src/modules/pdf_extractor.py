"""
PDF Image Extractor Module
Extracts images from PDF files for processing (OPTIMIZED FOR SPEED)
"""
import os
from PIL import Image
import PyPDF2
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

# Try to import pdf2image (requires poppler)
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

# Try to import pypdfium2 as fallback
try:
    import pypdfium2 as pdfium
    PYPDFIUM2_AVAILABLE = True
except ImportError:
    PYPDFIUM2_AVAILABLE = False


class PDFImageExtractor:
    """Extract images from PDF files"""
    
    def __init__(self, temp_dir='temp_images'):
        self.temp_dir = temp_dir
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
    
    def extract_images_from_pdf(self, pdf_path, dpi=100):
        """
        Extract all images from a PDF file (ULTRA FAST - parallel processing)
        
        Args:
            pdf_path (str): Path to the PDF file
            dpi (int): DPI for image conversion (100 para máxima velocidad, suficiente para Facebook)
            
        Returns:
            list: List of image paths
        """
        # Try pdf2image first (better quality if poppler is available)
        if PDF2IMAGE_AVAILABLE:
            try:
                return self._extract_with_pdf2image(pdf_path, dpi)
            except Exception as e:
                print(f"pdf2image failed: {e}")
                if PYPDFIUM2_AVAILABLE:
                    print("Falling back to pypdfium2...")
                    return self._extract_with_pypdfium2(pdf_path, dpi)
                raise
        
        # Fall back to pypdfium2
        elif PYPDFIUM2_AVAILABLE:
            return self._extract_with_pypdfium2(pdf_path, dpi)
        
        else:
            raise RuntimeError("No PDF rendering library available. Install pdf2image (requires poppler) or pypdfium2")
    
    def _extract_with_pdf2image(self, pdf_path, dpi):
        """Extract using pdf2image with parallel processing - ULTRA FAST"""
        # Usar máximo de hilos disponibles para conversión paralela
        max_workers = min(6, multiprocessing.cpu_count())  # Reducir a 6 para más estabilidad
        
        try:
            # Convertir todas las páginas en paralelo
            images = convert_from_path(
                pdf_path, 
                dpi=dpi,
                thread_count=max_workers,  # Máximo procesamiento paralelo
                fmt='png',
                use_pdftocairo=True  # Más rápido que pdftoppm
            )
        except Exception as e:
            print(f"Error con pdftocairo, intentando con pdftoppm: {e}")
            # Fallback sin pdftocairo
            images = convert_from_path(
                pdf_path, 
                dpi=dpi,
                thread_count=max_workers,
                fmt='png'
            )
        
        def save_image(args):
            """Guardar imagen individual"""
            i, image = args
            image_path = os.path.join(self.temp_dir, f'page_{i+1}.png')
            # Guardado ultra rápido sin compresión
            image.save(image_path, 'PNG', optimize=False, compress_level=0)
            print(f"✓ Página {i+1}/{len(images)}")
            return image_path
        
        # Guardar todas las imágenes en paralelo
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            image_paths = list(executor.map(save_image, enumerate(images)))
        
        return image_paths
    
    def _extract_with_pypdfium2(self, pdf_path, dpi):
        """Extract using pypdfium2 - optimized sequential (pypdfium2 no es thread-safe)"""
        pdf = pdfium.PdfDocument(pdf_path)
        num_pages = len(pdf)
        
        # Calcular escala una vez
        scale = dpi / 72
        image_paths = []
        
        # Procesar secuencialmente pero super rápido
        for page_num in range(num_pages):
            page = pdf[page_num]
            pil_image = page.render(scale=scale).to_pil()
            
            image_path = os.path.join(self.temp_dir, f'page_{page_num+1}.png')
            # Guardado ultra rápido sin optimización ni compresión
            pil_image.save(image_path, 'PNG', optimize=False, compress_level=0)
            image_paths.append(image_path)
            print(f"✓ Página {page_num+1}/{num_pages}")
        
        pdf.close()
        return image_paths
    
    def get_pdf_info(self, pdf_path):
        """
        Get basic information about the PDF
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            dict: PDF information
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                # Try to extract metadata
                metadata = pdf_reader.metadata
                
                return {
                    'num_pages': num_pages,
                    'metadata': metadata
                }
        except Exception as e:
            print(f"Error reading PDF info: {e}")
            return {'num_pages': 0, 'metadata': None}
    
    def cleanup(self):
        """Clean up temporary image files"""
        try:
            for file in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            print(f"Cleaned up temporary files in {self.temp_dir}")
        except Exception as e:
            print(f"Error cleaning up temporary files: {e}")
