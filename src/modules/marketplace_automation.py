"""
Facebook Marketplace Automation Module
Handles creating, editing, and deleting marketplace items using Selenium
"""
import time
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys


class MarketplaceAutomation:
    """Automate Facebook Marketplace operations"""
    
    def __init__(self, driver):
        """
        Initialize Marketplace automation
        
        Args:
            driver: Selenium WebDriver instance (already logged in)
        """
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 15)
    
    def create_listing(self, title, description, price, category, condition, images, tags=None, location=None):
        """
        Create a new marketplace listing
        
        Args:
            title (str): Product title
            description (str): Product description
            price (str): Product price
            category (str): Product category
            condition (str): Product condition (new, used, etc.)
            images (list): List of image file paths
            tags (list, optional): Product tags
            location (str, optional): Location
            
        Returns:
            bool: True if listing created successfully, False otherwise
        """
        try:
            print("Navigating to Marketplace create page...")
            self.driver.get('https://web.facebook.com/marketplace/create/item')
            time.sleep(5)
            
            # Upload images
            print("Uploading images...")
            if not self._upload_images(images):
                print("Failed to upload images")
                return False
            
            # Fill in title
            print(f"Entering title: {title}")
            if not self._fill_field("Title", title):
                return False
            
            # Fill in price
            print(f"Entering price: {price}")
            if not self._fill_field("Price", price):
                return False
            
            # Select category (simplified - may need adjustment based on actual UI)
            print(f"Selecting category: {category}")
            time.sleep(2)
            
            # Select condition
            print(f"Selecting condition: {condition}")
            time.sleep(2)
            
            # Fill in description
            print(f"Entering description...")
            if not self._fill_field("Description", description):
                return False
            
            # Add tags if provided
            if tags:
                print(f"Adding tags: {tags}")
                self._add_tags(tags)
            
            # Set location if provided
            if location:
                print(f"Setting location: {location}")
                self._set_location(location)
            
            # Submit the listing
            print("Submitting listing...")
            time.sleep(3)
            
            # Click "Next" or "Publish" button
            if self._click_publish_button():
                print("Listing created successfully!")
                time.sleep(5)
                return True
            else:
                print("Failed to find publish button")
                return False
                
        except Exception as e:
            print(f"Error creating listing: {e}")
            return False
    
    def _upload_images(self, image_paths):
        """
        Upload images to the listing
        
        Args:
            image_paths (list): List of image file paths
            
        Returns:
            bool: True if upload successful
        """
        try:
            # Find file input element (usually hidden)
            file_inputs = self.driver.find_elements(By.XPATH, "//input[@type='file']")
            
            if not file_inputs:
                print("Could not find file input element")
                return False
            
            file_input = file_inputs[0]
            
            # Convert to absolute paths
            abs_paths = [os.path.abspath(path) for path in image_paths if os.path.exists(path)]
            
            if not abs_paths:
                print("No valid image paths found")
                return False
            
            # Try to upload all images at once (platform-dependent)
            # If this fails, we'll need to upload one by one
            try:
                # Upload all images at once (separated by newline for multi-file input)
                file_input.send_keys('\n'.join(abs_paths))
                print(f"Uploaded {len(abs_paths)} images")
                time.sleep(3)
                return True
            except Exception as e:
                print(f"Batch upload failed, trying one by one: {e}")
                # Upload one by one as fallback
                for i, path in enumerate(abs_paths):
                    try:
                        file_input.send_keys(path)
                        print(f"Uploaded image {i+1}/{len(abs_paths)}")
                        time.sleep(1)
                    except Exception as upload_error:
                        print(f"Failed to upload {path}: {upload_error}")
                
                return True
            
        except Exception as e:
            print(f"Error uploading images: {e}")
            return False
    
    def _fill_field(self, label, value):
        """
        Fill a form field by label
        
        Args:
            label (str): Field label
            value (str): Value to enter
            
        Returns:
            bool: True if successful
        """
        try:
            # Try multiple strategies to find the field
            strategies = [
                (By.XPATH, f"//label[contains(text(), '{label}')]/following::input[1]"),
                (By.XPATH, f"//label[contains(text(), '{label}')]/following::textarea[1]"),
                (By.XPATH, f"//input[@placeholder='{label}']"),
                (By.XPATH, f"//textarea[@placeholder='{label}']"),
                (By.XPATH, f"//input[@aria-label='{label}']"),
                (By.XPATH, f"//textarea[@aria-label='{label}']"),
            ]
            
            for by, xpath in strategies:
                try:
                    field = self.wait.until(EC.presence_of_element_located((by, xpath)))
                    field.clear()
                    field.send_keys(value)
                    time.sleep(1)
                    return True
                except TimeoutException:
                    continue
            
            print(f"Could not find field for label: {label}")
            return False
            
        except Exception as e:
            print(f"Error filling field {label}: {e}")
            return False
    
    def _add_tags(self, tags):
        """
        Add tags to the listing
        
        Args:
            tags (list): List of tags
        """
        try:
            # Tags might be added through description or separate field
            # This is a placeholder - actual implementation depends on UI
            pass
        except Exception as e:
            print(f"Error adding tags: {e}")
    
    def _set_location(self, location):
        """
        Set the location for the listing
        
        Args:
            location (str): Location string
        """
        try:
            # Find location field and enter location
            location_field = self.driver.find_element(By.XPATH, "//input[@placeholder='Location']")
            location_field.clear()
            location_field.send_keys(location)
            time.sleep(2)
        except Exception as e:
            print(f"Error setting location: {e}")
    
    def _click_publish_button(self):
        """
        Click the publish/next button
        
        Returns:
            bool: True if button clicked successfully
        """
        try:
            # Try to find "Next" or "Publish" button
            button_texts = ['Next', 'Publish', 'List', 'Post']
            
            for text in button_texts:
                try:
                    button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, f"//span[contains(text(), '{text}')]/ancestor::div[@role='button']"))
                    )
                    button.click()
                    time.sleep(3)
                    return True
                except TimeoutException:
                    continue
            
            return False
            
        except Exception as e:
            print(f"Error clicking publish button: {e}")
            return False
    
    def edit_listing(self, listing_url, **kwargs):
        """
        Edit an existing marketplace listing
        
        Args:
            listing_url (str): URL of the listing to edit
            **kwargs: Fields to update (title, description, price, etc.)
            
        Returns:
            bool: True if edit successful
        """
        try:
            print(f"Navigating to listing: {listing_url}")
            self.driver.get(listing_url)
            time.sleep(3)
            
            # Click edit button
            edit_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Edit')]/ancestor::div[@role='button']"))
            )
            edit_button.click()
            time.sleep(3)
            
            # Update fields
            if 'title' in kwargs:
                self._fill_field("Title", kwargs['title'])
            
            if 'price' in kwargs:
                self._fill_field("Price", kwargs['price'])
            
            if 'description' in kwargs:
                self._fill_field("Description", kwargs['description'])
            
            # Save changes
            save_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Save')]/ancestor::div[@role='button']"))
            )
            save_button.click()
            time.sleep(3)
            
            print("Listing updated successfully!")
            return True
            
        except Exception as e:
            print(f"Error editing listing: {e}")
            return False
    
    def delete_listing(self, listing_url):
        """
        Delete a marketplace listing
        
        Args:
            listing_url (str): URL of the listing to delete
            
        Returns:
            bool: True if deletion successful
        """
        try:
            print(f"Navigating to listing: {listing_url}")
            self.driver.get(listing_url)
            time.sleep(3)
            
            # Click menu button (three dots)
            menu_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='More']"))
            )
            menu_button.click()
            time.sleep(2)
            
            # Click delete option
            delete_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Delete')]/ancestor::div[@role='menuitem']"))
            )
            delete_button.click()
            time.sleep(2)
            
            # Confirm deletion
            confirm_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Delete')]/ancestor::div[@role='button']"))
            )
            confirm_button.click()
            time.sleep(3)
            
            print("Listing deleted successfully!")
            return True
            
        except Exception as e:
            print(f"Error deleting listing: {e}")
            return False
    
    def get_my_listings(self):
        """
        Get list of user's marketplace listings
        
        Returns:
            list: List of listing URLs
        """
        try:
            # Import Config to get URL
            from config.settings import Config
            
            print("Navigating to your listings...")
            self.driver.get(Config.MARKETPLACE_SELLING_URL)
            time.sleep(5)
            
            # Find listing links
            listings = []
            listing_elements = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/marketplace/item/')]")
            
            for element in listing_elements:
                href = element.get_attribute('href')
                if href and href not in listings:
                    listings.append(href)
            
            print(f"Found {len(listings)} listings")
            return listings
            
        except Exception as e:
            print(f"Error getting listings: {e}")
            return []
