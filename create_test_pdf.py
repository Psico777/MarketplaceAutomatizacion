"""
Script to create a test PDF with a sample product image
"""
from PIL import Image, ImageDraw, ImageFont
from PyPDF2 import PdfWriter
import io

def create_test_pdf():
    """Create a test PDF with product images"""
    
    # Create images for a sample product (laptop)
    images = []
    
    # Image 1: Main product image
    img1 = Image.new('RGB', (800, 600), color='white')
    draw1 = ImageDraw.Draw(img1)
    
    # Draw a simple laptop representation
    # Screen
    draw1.rectangle([200, 100, 600, 400], outline='black', width=5, fill='lightblue')
    draw1.text((350, 230), "LAPTOP", fill='black')
    
    # Keyboard base
    draw1.polygon([150, 400, 650, 400, 700, 500, 100, 500], outline='black', width=5, fill='lightgray')
    
    # Draw some keys
    for row in range(4):
        for col in range(12):
            x = 150 + col * 40
            y = 420 + row * 20
            draw1.rectangle([x, y, x+30, y+15], outline='darkgray', width=1, fill='white')
    
    draw1.text((250, 520), "Test Product - Gaming Laptop", fill='black')
    draw1.text((280, 550), "High Performance Model", fill='darkgray')
    
    images.append(img1)
    
    # Image 2: Side view
    img2 = Image.new('RGB', (800, 600), color='white')
    draw2 = ImageDraw.Draw(img2)
    
    # Draw side view
    draw2.rectangle([200, 250, 600, 350], outline='black', width=5, fill='lightgray')
    draw2.text((300, 280), "Side View - Slim Design", fill='black')
    draw2.text((250, 400), "Specifications:", fill='black')
    draw2.text((250, 430), "• Intel Core i7 Processor", fill='darkgray')
    draw2.text((250, 460), "• 16GB RAM", fill='darkgray')
    draw2.text((250, 490), "• 512GB SSD", fill='darkgray')
    draw2.text((250, 520), "• NVIDIA RTX Graphics", fill='darkgray')
    
    images.append(img2)
    
    # Image 3: Accessories
    img3 = Image.new('RGB', (800, 600), color='white')
    draw3 = ImageDraw.Draw(img3)
    
    draw3.text((300, 100), "Package Includes:", fill='black')
    
    # Charger
    draw3.rectangle([200, 150, 300, 200], outline='black', width=3, fill='gray')
    draw3.text((180, 210), "Charger", fill='black')
    
    # Mouse
    draw3.ellipse([350, 160, 430, 240], outline='black', width=3, fill='lightgray')
    draw3.text((360, 250), "Mouse", fill='black')
    
    # Bag
    draw3.rectangle([480, 140, 600, 260], outline='black', width=3, fill='brown')
    draw3.text((510, 270), "Laptop Bag", fill='black')
    
    draw3.text((250, 350), "Condition: Excellent", fill='green')
    draw3.text((250, 380), "Price: Negotiable", fill='blue')
    draw3.text((250, 410), "Contact for more details!", fill='black')
    
    images.append(img3)
    
    # Create PDF
    pdf_writer = PdfWriter()
    
    for img in images:
        # Convert PIL Image to PDF
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        # For simplicity, save as individual images first
        # then we'll convert them properly
    
    # Save images as PNG first
    for i, img in enumerate(images):
        img.save(f'temp_page_{i}.png')
    
    print("✓ Created 3 product images")
    print("Converting to PDF...")
    
    # Convert images to PDF
    img_list = []
    for i in range(len(images)):
        temp_img = Image.open(f'temp_page_{i}.png')
        img_rgb = temp_img.convert('RGB')
        img_list.append(img_rgb)
    
    # Save as PDF
    img_list[0].save('product_test.pdf', save_all=True, append_images=img_list[1:])
    
    # Clean up temp files
    import os
    for i in range(len(images)):
        os.remove(f'temp_page_{i}.png')
    
    print("✓ PDF created successfully: product_test.pdf")
    print("\nYou can now run:")
    print("python main.py create --pdf product_test.pdf --category Electronics --condition Used")

if __name__ == '__main__':
    create_test_pdf()
