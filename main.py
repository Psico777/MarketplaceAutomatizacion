"""
Main script for Facebook Marketplace Automation
Orchestrates PDF processing, AI analysis, and marketplace listing
"""
import sys
import os
import argparse

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.settings import Config
from modules.pdf_extractor import PDFImageExtractor
from modules.ai_analyzer import AIImageAnalyzer
from modules.facebook_auth import FacebookAuthenticator
from modules.marketplace_automation import MarketplaceAutomation


class MarketplaceAutomationSystem:
    """Main system to automate Facebook Marketplace listings"""
    
    def __init__(self):
        """Initialize the automation system"""
        # Validate configuration
        Config.validate()
        
        # Initialize components
        self.pdf_extractor = PDFImageExtractor(Config.TEMP_DIR)
        self.ai_analyzer = AIImageAnalyzer(
            api_key=Config.GEMINI_API_KEY,
            model=Config.AI_MODEL_IMAGE,
            max_size=Config.MAX_IMAGE_SIZE
        )
        self.authenticator = FacebookAuthenticator(
            email=Config.FACEBOOK_EMAIL,
            password=Config.FACEBOOK_PASSWORD,
            two_fa_secret=Config.FACEBOOK_2FA_SECRET,
            headless=Config.HEADLESS,
            implicit_wait=Config.IMPLICIT_WAIT
        )
        self.marketplace = None
    
    def process_pdf_and_create_listing(self, pdf_path, category='Other', condition='Used', location=None):
        """
        Complete workflow: Extract images from PDF, analyze with AI, create listing
        
        Args:
            pdf_path (str): Path to PDF file
            category (str): Product category
            condition (str): Product condition
            location (str, optional): Location for listing
            
        Returns:
            bool: True if successful
        """
        try:
            print("=" * 50)
            print("Starting Facebook Marketplace Automation")
            print("=" * 50)
            
            # Step 1: Extract images from PDF
            print("\n[1/5] Extracting images from PDF...")
            image_paths = self.pdf_extractor.extract_images_from_pdf(pdf_path)
            
            if not image_paths:
                print("Error: No images extracted from PDF")
                return False
            
            print(f"✓ Extracted {len(image_paths)} images")
            
            # Step 2: Analyze images with AI
            print("\n[2/5] Analyzing images with Gemini AI...")
            product_info = self.ai_analyzer.analyze_multiple_images(image_paths)
            
            if not product_info:
                print("Error: Failed to analyze images")
                return False
            
            print(f"✓ AI Analysis complete:")
            print(f"  - Title: {product_info['title']}")
            print(f"  - Price: ${product_info['price']}")
            print(f"  - Description: {product_info['description'][:100]}...")
            print(f"  - Tags: {', '.join(product_info['tags'])}")
            
            # Step 3: Login to Facebook
            print("\n[3/5] Logging into Facebook...")
            if not self.authenticator.login():
                print("Error: Failed to login to Facebook")
                return False
            
            print("✓ Logged in successfully")
            
            # Step 4: Create marketplace listing
            print("\n[4/5] Creating marketplace listing...")
            self.marketplace = MarketplaceAutomation(self.authenticator.driver)
            
            success = self.marketplace.create_listing(
                title=product_info['title'],
                description=product_info['description'],
                price=product_info['price'],
                category=category,
                condition=condition,
                images=image_paths,
                tags=product_info['tags'],
                location=location
            )
            
            if not success:
                print("Error: Failed to create listing")
                return False
            
            print("✓ Listing created successfully!")
            
            # Step 5: Cleanup
            print("\n[5/5] Cleaning up...")
            self.pdf_extractor.cleanup()
            print("✓ Cleanup complete")
            
            print("\n" + "=" * 50)
            print("Automation completed successfully!")
            print("=" * 50)
            
            return True
            
        except Exception as e:
            print(f"\nError in automation process: {e}")
            return False
        finally:
            # Keep browser open for a bit to see results
            import time
            time.sleep(10)
    
    def edit_listing(self, listing_url, **kwargs):
        """
        Edit an existing listing
        
        Args:
            listing_url (str): URL of listing to edit
            **kwargs: Fields to update
            
        Returns:
            bool: True if successful
        """
        try:
            print("Editing listing...")
            
            # Login if not already
            if not self.authenticator.driver:
                if not self.authenticator.login():
                    return False
            
            self.marketplace = MarketplaceAutomation(self.authenticator.driver)
            return self.marketplace.edit_listing(listing_url, **kwargs)
            
        except Exception as e:
            print(f"Error editing listing: {e}")
            return False
    
    def delete_listing(self, listing_url):
        """
        Delete a listing
        
        Args:
            listing_url (str): URL of listing to delete
            
        Returns:
            bool: True if successful
        """
        try:
            print("Deleting listing...")
            
            # Login if not already
            if not self.authenticator.driver:
                if not self.authenticator.login():
                    return False
            
            self.marketplace = MarketplaceAutomation(self.authenticator.driver)
            return self.marketplace.delete_listing(listing_url)
            
        except Exception as e:
            print(f"Error deleting listing: {e}")
            return False
    
    def list_my_listings(self):
        """
        List all user's marketplace listings
        
        Returns:
            list: List of listing URLs
        """
        try:
            print("Fetching your listings...")
            
            # Login if not already
            if not self.authenticator.driver:
                if not self.authenticator.login():
                    return []
            
            self.marketplace = MarketplaceAutomation(self.authenticator.driver)
            return self.marketplace.get_my_listings()
            
        except Exception as e:
            print(f"Error listing items: {e}")
            return []
    
    def close(self):
        """Close the automation system"""
        if self.authenticator:
            self.authenticator.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Facebook Marketplace Automation')
    parser.add_argument('action', choices=['create', 'edit', 'delete', 'list'],
                        help='Action to perform')
    parser.add_argument('--pdf', type=str, help='Path to PDF file (for create)')
    parser.add_argument('--url', type=str, help='Listing URL (for edit/delete)')
    parser.add_argument('--title', type=str, help='New title (for edit)')
    parser.add_argument('--price', type=str, help='New price (for edit)')
    parser.add_argument('--description', type=str, help='New description (for edit)')
    parser.add_argument('--category', type=str, default='Other', help='Product category')
    parser.add_argument('--condition', type=str, default='Used', help='Product condition')
    parser.add_argument('--location', type=str, help='Location for listing')
    
    args = parser.parse_args()
    
    system = MarketplaceAutomationSystem()
    
    try:
        if args.action == 'create':
            if not args.pdf:
                print("Error: --pdf is required for create action")
                return
            
            success = system.process_pdf_and_create_listing(
                pdf_path=args.pdf,
                category=args.category,
                condition=args.condition,
                location=args.location
            )
            
            if not success:
                sys.exit(1)
        
        elif args.action == 'edit':
            if not args.url:
                print("Error: --url is required for edit action")
                return
            
            updates = {}
            if args.title:
                updates['title'] = args.title
            if args.price:
                updates['price'] = args.price
            if args.description:
                updates['description'] = args.description
            
            if not updates:
                print("Error: At least one field to update is required")
                return
            
            success = system.edit_listing(args.url, **updates)
            
            if not success:
                sys.exit(1)
        
        elif args.action == 'delete':
            if not args.url:
                print("Error: --url is required for delete action")
                return
            
            success = system.delete_listing(args.url)
            
            if not success:
                sys.exit(1)
        
        elif args.action == 'list':
            listings = system.list_my_listings()
            
            if listings:
                print("\nYour listings:")
                for i, url in enumerate(listings, 1):
                    print(f"{i}. {url}")
            else:
                print("No listings found")
    
    finally:
        system.close()


if __name__ == '__main__':
    main()
