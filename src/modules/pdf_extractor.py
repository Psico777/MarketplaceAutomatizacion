"""
PDF Image Extractor Module
Extracts images from PDF files for processing
"""
import os
from PIL import Image
from pdf2image import convert_from_path
import PyPDF2


class PDFImageExtractor:
    """Extract images from PDF files"""
    
    def __init__(self, temp_dir='temp_images'):
        self.temp_dir = temp_dir
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
    
    def extract_images_from_pdf(self, pdf_path, dpi=300):
        """
        Extract all images from a PDF file
        
        Args:
            pdf_path (str): Path to the PDF file
            dpi (int): DPI for image conversion
            
        Returns:
            list: List of image paths
        """
        try:
            # Convert PDF pages to images
            images = convert_from_path(pdf_path, dpi=dpi)
            image_paths = []
            
            for i, image in enumerate(images):
                image_path = os.path.join(self.temp_dir, f'page_{i+1}.png')
                image.save(image_path, 'PNG')
                image_paths.append(image_path)
                print(f"Extracted page {i+1} to {image_path}")
            
            return image_paths
        
        except Exception as e:
            print(f"Error extracting images from PDF: {e}")
            raise
    
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
