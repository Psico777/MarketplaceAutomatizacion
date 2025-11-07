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
        Create a new marketplace listing - UPDATED with exact navigation flow
        
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
            self.driver.get('https://www.facebook.com/marketplace/create/item')
            
            # Maximize window for better visibility
            self.driver.maximize_window()
            time.sleep(0.2)  # MÍNIMO
            
            # Take screenshot for debugging
            self.driver.save_screenshot('screenshots/marketplace_create.png')
            print("Screenshot saved: screenshots/marketplace_create.png")
            
            # Upload images FIRST
            print("Uploading images...")
            if not self._upload_images_modern(images):
                print("⚠ Warning: Image upload may have failed, continuing...")
            
            time.sleep(0.2)  # MÍNIMO
            
            # STEP 1: Fill in title
            print(f"[1/7] Entering title: {title[:50]}...")
            if not self._fill_title_field(title):
                print("Failed to fill title")
                return False
            
            # STEP 2: TAB to price and fill
            print(f"[2/7] Entering price: ${price}")
            active = self.driver.switch_to.active_element
            active.send_keys(Keys.TAB)
            time.sleep(0.1)
            active = self.driver.switch_to.active_element
            active.clear()
            time.sleep(0.1)
            active.send_keys(str(price))
            time.sleep(0.1)
            print("  ✓ Price entered")
            
            # STEP 3: TAB to category, ENTER to open list, 14 TABs, ENTER to select
            print(f"[3/7] Selecting category (Electronics)...")
            active = self.driver.switch_to.active_element
            active.send_keys(Keys.TAB)
            time.sleep(0.1)
            active = self.driver.switch_to.active_element
            active.send_keys(Keys.ENTER)  # Open category list
            time.sleep(0.2)
            
            # Navigate with 14 TABs to Electronics
            for i in range(14):
                active = self.driver.switch_to.active_element
                active.send_keys(Keys.TAB)
                time.sleep(0.1)
            
            active = self.driver.switch_to.active_element
            active.send_keys(Keys.ENTER)  # Select category
            time.sleep(0.2)
            print("  ✓ Category selected")
            
            # STEP 4: TAB to condition (estado), type 'n', ENTER for "Nuevo"
            print(f"[4/7] Setting condition to 'Nuevo'...")
            active = self.driver.switch_to.active_element
            active.send_keys(Keys.TAB)
            time.sleep(0.1)
            active = self.driver.switch_to.active_element
            active.send_keys('n')  # Type 'n' for Nuevo
            time.sleep(0.1)
            active.send_keys(Keys.ENTER)
            time.sleep(0.2)
            print("  ✓ Condition set to 'Nuevo'")
            
            # STEP 5: 4 TABs to description
            print(f"[5/7] Entering description...")
            for i in range(4):
                active = self.driver.switch_to.active_element
                active.send_keys(Keys.TAB)
                time.sleep(0.1)
            
            active = self.driver.switch_to.active_element
            active.send_keys(description)
            time.sleep(0.2)
            print("  ✓ Description entered")
            
            # STEP 6: 2 TABs to tags/etiquetas
            print(f"[6/7] Adding tags...")
            for i in range(2):
                active = self.driver.switch_to.active_element
                active.send_keys(Keys.TAB)
                time.sleep(0.1)
            
            # Add default tags + AI tags
            default_tags = ['remate', 'oferta']
            all_tags = default_tags + (tags[:6] if tags else [])
            
            for tag in all_tags:
                active = self.driver.switch_to.active_element
                active.send_keys(tag)
                time.sleep(0.1)
                active.send_keys(Keys.ENTER)
                time.sleep(0.1)
                print(f"  ✓ Tag added: {tag}")
            
            print(f"  ✓ Added {len(all_tags)} tags")
            
            # STEP 7: 15 TABs to "Siguiente" button and ENTER
            print(f"[7/7] Clicking 'Siguiente' button...")
            for i in range(15):
                active = self.driver.switch_to.active_element
                active.send_keys(Keys.TAB)
                time.sleep(0.1)
            
            active = self.driver.switch_to.active_element
            active.send_keys(Keys.ENTER)
            time.sleep(0.2)
            print("  ✓ 'Siguiente' clicked")
            
            # STEP 8: Click "Publicar" button
            print(f"[8/8] Clicking 'Publicar' button...")
            try:
                # Wait for the Publicar button to be clickable - CORRECT XPATH
                publicar_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div[1]/div/div[4]/div[2]/div/div"))
                )
                publicar_button.click()
                time.sleep(0.2)
                print("  ✓ 'Publicar' clicked - Listing published!")
            except Exception as e:
                print(f"  ⚠ Could not click Publicar button with XPath, trying alternative...")
                # Try clicking via TAB navigation as fallback
                try:
                    active = self.driver.switch_to.active_element
                    active.send_keys(Keys.TAB)
                    time.sleep(0.1)
                    active = self.driver.switch_to.active_element
                    active.send_keys(Keys.ENTER)
                    time.sleep(0.2)
                    print("  ✓ 'Publicar' clicked via TAB")
                except:
                    print(f"  ✗ Failed to click Publicar: {e}")
            
            # Take success screenshot
            self.driver.save_screenshot('screenshots/listing_published.png')
            print("✓ Listing creation completed!")
            
            return True
                
        except Exception as e:
            print(f"Error creating listing: {e}")
            import traceback
            traceback.print_exc()
            self.driver.save_screenshot('screenshots/listing_error.png')
            return False
    
    def _upload_images_modern(self, image_paths):
        """
        Upload images to the listing - Modern Facebook UI
        
        Args:
            image_paths (list): List of image file paths
            
        Returns:
            bool: True if upload successful
        """
        try:
            # Find file input element (usually hidden)
            file_inputs = self.driver.find_elements(By.XPATH, "//input[@type='file' and @accept]")
            
            if not file_inputs:
                print("⚠ Could not find file input element, trying alternative...")
                file_inputs = self.driver.find_elements(By.XPATH, "//input[@type='file']")
            
            if not file_inputs:
                print("✗ No file input found")
                return False
            
            file_input = file_inputs[0]
            
            # Convert to absolute paths
            abs_paths = [os.path.abspath(path) for path in image_paths if os.path.exists(path)]
            
            if not abs_paths:
                print("✗ No valid image paths found")
                return False
            
            print(f"Uploading {len(abs_paths)} image(s)...")
            
            # Upload images one by one for better reliability
            for i, path in enumerate(abs_paths, 1):
                try:
                    file_input.send_keys(path)
                    print(f"  ✓ Uploaded image {i}/{len(abs_paths)}: {os.path.basename(path)}")
                    time.sleep(0.2)
                except Exception as upload_error:
                    print(f"  ✗ Failed to upload {path}: {upload_error}")
            
            time.sleep(0.2)
            return True
            
        except Exception as e:
            print(f"Error uploading images: {e}")
            return False
    
    def _fill_title_field(self, title):
        """Fill title field using TAB navigation (16 TABs)"""
        try:
            print(f"    Using TAB method (16 TABs from upload)...")
            
            # Esperar después de subir imágenes
            time.sleep(0.2)  # Reducido
            
            # Hacer 16 TABs desde donde estemos (RÁPIDO)
            for i in range(14):
                active = self.driver.switch_to.active_element
                active.send_keys(Keys.TAB)
                time.sleep(0.1)
            
            # Ahora deberíamos estar en el campo de título
            active = self.driver.switch_to.active_element
            
            # NO hacer clear(), simplemente escribir directamente
            active.send_keys(title)
            time.sleep(0.1)
            
            # Verificar que se ingresó el texto
            current_value = active.get_attribute('value')
            if current_value and len(current_value) > 0:
                print(f"  ✓ Title entered successfully: {current_value[:30]}...")
                return True
            else:
                print(f"  ✗ Title field is empty after entering text")
                return False
            
        except Exception as e:
            print(f"  ✗ Error filling title: {e}")
            return False
    
    def _fill_price_with_tab(self, price):
        """Fill price field by TABbing from title or finding directly"""
        try:
            # First, try TAB method
            try:
                active = self.driver.switch_to.active_element
                active.send_keys(Keys.TAB)
                time.sleep(0.8)
                
                active = self.driver.switch_to.active_element
                active.clear()
                time.sleep(0.3)
                active.send_keys(str(price))
                print(f"  ✓ Price entered: ${price} (TAB method)")
                return True
            except:
                pass
            
            # If TAB fails, try to find price field directly
            price_xpaths = [
                "//input[@placeholder='Precio']",
                "//input[@placeholder='Price']",
                "//input[@aria-label='Precio']",
                "//input[@aria-label='Price']",
                "//input[@type='text' and contains(@placeholder, 'price')]",
                "//input[@type='number']"
            ]
            
            for xpath in price_xpaths:
                try:
                    price_field = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    price_field.click()
                    time.sleep(0.3)
                    price_field.clear()
                    time.sleep(0.3)
                    price_field.send_keys(str(price))
                    print(f"  ✓ Price entered: ${price} (direct method)")
                    return True
                except:
                    continue
            
            print(f"  ⚠ Could not fill price field")
            return False
            
        except Exception as e:
            print(f"  ✗ Error filling price: {e}")
            return False
    
    def _fill_description_field(self, description):
        """Fill description field - improved"""
        try:
            # Multiple attempts to find description field
            desc_xpaths = [
                "//textarea[@placeholder='Descripción']",
                "//textarea[@placeholder='Description']",
                "//textarea[@aria-label='Descripción']",
                "//textarea[@aria-label='Description']",
                "//div[@contenteditable='true' and @role='textbox']",
                "//textarea[contains(@class, 'description')]"
            ]
            
            for xpath in desc_xpaths:
                try:
                    desc_field = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    
                    # Scroll into view
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", desc_field)
                    time.sleep(0.5)
                    
                    # Click and fill
                    desc_field.click()
                    time.sleep(0.3)
                    
                    # For contenteditable divs
                    if desc_field.get_attribute('contenteditable') == 'true':
                        desc_field.send_keys(Keys.CONTROL + "a")
                        time.sleep(0.2)
                        desc_field.send_keys(description)
                    else:
                        desc_field.clear()
                        time.sleep(0.2)
                        desc_field.send_keys(description)
                    
                    print(f"  ✓ Description entered")
                    return True
                except:
                    continue
            
            print(f"  ⚠ Could not fill description field")
            return False
            
        except Exception as e:
            print(f"  ⚠ Error filling description: {e}")
            return False
    
    def _navigate_with_tab(self, times=1):
        """Navigate fields using TAB key"""
        try:
            active = self.driver.switch_to.active_element
            for _ in range(times):
                active.send_keys(Keys.TAB)
                time.sleep(0.3)
        except Exception as e:
            print(f"  ⚠ TAB navigation issue: {e}")
    
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
