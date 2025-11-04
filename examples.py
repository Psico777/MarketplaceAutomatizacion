"""
Example usage script for Facebook Marketplace Automation
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.settings import Config
from modules.pdf_extractor import PDFImageExtractor
from modules.ai_analyzer import AIImageAnalyzer
from modules.facebook_auth import FacebookAuthenticator
from modules.marketplace_automation import MarketplaceAutomation


def example_pdf_to_listing():
    """
    Example: Complete workflow from PDF to Marketplace listing
    """
    print("=== Example: PDF to Marketplace Listing ===\n")
    
    # Initialize components
    pdf_extractor = PDFImageExtractor(Config.TEMP_DIR)
    ai_analyzer = AIImageAnalyzer(
        api_key=Config.GEMINI_API_KEY,
        model=Config.AI_MODEL_IMAGE
    )
    
    # 1. Extract images from PDF
    print("1. Extracting images from PDF...")
    pdf_path = "example_product.pdf"  # Replace with your PDF
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        print("Please create a PDF file with product images first.")
        return
    
    image_paths = pdf_extractor.extract_images_from_pdf(pdf_path)
    print(f"   Extracted {len(image_paths)} images\n")
    
    # 2. Analyze with AI
    print("2. Analyzing images with Gemini AI...")
    product_info = ai_analyzer.analyze_multiple_images(image_paths)
    
    print(f"   Title: {product_info['title']}")
    print(f"   Price: ${product_info['price']}")
    print(f"   Description: {product_info['description'][:100]}...")
    print(f"   Tags: {', '.join(product_info['tags'])}\n")
    
    # 3. Login to Facebook
    print("3. Logging into Facebook...")
    authenticator = FacebookAuthenticator(
        email=Config.FACEBOOK_EMAIL,
        password=Config.FACEBOOK_PASSWORD,
        two_fa_secret=Config.FACEBOOK_2FA_SECRET,
        headless=Config.HEADLESS
    )
    
    if not authenticator.login():
        print("   Failed to login")
        return
    
    print("   Logged in successfully\n")
    
    # 4. Create listing
    print("4. Creating marketplace listing...")
    marketplace = MarketplaceAutomation(authenticator.driver)
    
    success = marketplace.create_listing(
        title=product_info['title'],
        description=product_info['description'],
        price=product_info['price'],
        category="Other",
        condition="Used",
        images=image_paths,
        tags=product_info['tags']
    )
    
    if success:
        print("   Listing created successfully!\n")
    else:
        print("   Failed to create listing\n")
    
    # Cleanup
    pdf_extractor.cleanup()
    
    # Keep browser open to see results
    import time
    time.sleep(10)
    authenticator.close()


def example_edit_listing():
    """
    Example: Edit an existing listing
    """
    print("=== Example: Edit Listing ===\n")
    
    listing_url = "https://facebook.com/marketplace/item/123456789"  # Replace with actual URL
    
    authenticator = FacebookAuthenticator(
        email=Config.FACEBOOK_EMAIL,
        password=Config.FACEBOOK_PASSWORD,
        two_fa_secret=Config.FACEBOOK_2FA_SECRET
    )
    
    if authenticator.login():
        marketplace = MarketplaceAutomation(authenticator.driver)
        
        success = marketplace.edit_listing(
            listing_url,
            title="Updated Product Title",
            price="99"
        )
        
        if success:
            print("Listing updated successfully!")
        
        import time
        time.sleep(10)
        authenticator.close()


def example_list_items():
    """
    Example: List all your marketplace items
    """
    print("=== Example: List Your Items ===\n")
    
    authenticator = FacebookAuthenticator(
        email=Config.FACEBOOK_EMAIL,
        password=Config.FACEBOOK_PASSWORD,
        two_fa_secret=Config.FACEBOOK_2FA_SECRET
    )
    
    if authenticator.login():
        marketplace = MarketplaceAutomation(authenticator.driver)
        listings = marketplace.get_my_listings()
        
        print(f"Found {len(listings)} listings:\n")
        for i, url in enumerate(listings, 1):
            print(f"{i}. {url}")
        
        import time
        time.sleep(10)
        authenticator.close()


if __name__ == '__main__':
    print("Facebook Marketplace Automation - Examples\n")
    print("Choose an example to run:")
    print("1. Complete workflow: PDF to Marketplace")
    print("2. Edit existing listing")
    print("3. List all your items")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ")
    
    if choice == '1':
        example_pdf_to_listing()
    elif choice == '2':
        example_edit_listing()
    elif choice == '3':
        example_list_items()
    else:
        print("Exiting...")
