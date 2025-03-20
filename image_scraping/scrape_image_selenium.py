from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os
import time
from urllib.parse import quote
from io import BytesIO
from PIL import Image
import requests

def extract_meal_image_selenium(meal_name):
    """
    Searches for an image of a meal using Selenium with Google Images and returns the image object.
    
    Parameters:
        meal_name (str): Name of the meal to search for
        
    Returns:
        PIL.Image.Image: Image object if found, None otherwise
    """
    try:
        print(f"Searching for image of: {meal_name}")
        
        # Format the search query - add "food" to get better results
        search_query = quote(f"{meal_name} food dish")
        
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Initialize the Chrome driver
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        # Navigate to Google Images
        driver.get(f"https://www.google.com/search?q={search_query}&tbm=isch")
        
        # Wait for the images to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "img.rg_i"))
        )
        
        # Find the first image
        images = driver.find_elements(By.CSS_SELECTOR, "img.rg_i")
        if not images:
            print(f"  No images found for {meal_name}")
            driver.quit()
            return None
        
        # Get the source of the first image
        first_image = images[0]
        if first_image.get_attribute("src"):
            img_url = first_image.get_attribute("src")
        else:
            # If src is not available, try data-src or other attributes
            img_url = first_image.get_attribute("data-src")
            
            # If still no URL, try to get it from the style attribute
            if not img_url:
                # Click on the image to load the full version
                first_image.click()
                
                # Wait for the large image to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "img.n3VNCb"))
                )
                
                # Get the URL of the large image
                large_img = driver.find_element(By.CSS_SELECTOR, "img.n3VNCb")
                img_url = large_img.get_attribute("src")
        
        driver.quit()
        
        if img_url:
            # Check if it's a base64 encoded image
            if img_url.startswith('data:image'):
                # Extract the base64 data
                img_data = img_url.split(',')[1]
                img = Image.open(BytesIO(base64.b64decode(img_data)))
            else:
                # Download the image
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                img_response = requests.get(img_url, headers=headers)
                img = Image.open(BytesIO(img_response.content))
            
            return img
        else:
            print(f"  No valid image URL found for {meal_name}")
            return None
            
    except Exception as e:
        print(f"  Error finding image for {meal_name}: {str(e)}")
        # Make sure to quit the driver in case of an exception
        try:
            driver.quit()
        except:
            pass
        return None

if __name__ == "__main__":
    # Create directory for images
    images_dir = "meal_images"
    os.makedirs(images_dir, exist_ok=True)
    
    meal_names = [
        "Spaghetti Bolognese",
        "Caesar Salad",
        "Chicken Curry",
        "Vegetable Stir Fry"
    ]
    
    # Process each meal and save images
    meal_to_image_path = {}
    for meal_name in meal_names:
        img = extract_meal_image_selenium(meal_name)
        if img:
            # Create a safe filename
            safe_filename = "".join(c if c.isalnum() else "_" for c in meal_name)
            img_path = os.path.join(images_dir, f"{safe_filename}.jpg")
            
            # Save the image
            img.save(img_path)
            print(f"  Image saved to {img_path}")
            meal_to_image_path[meal_name] = img_path
            
        # Be nice to the server with a small delay
        time.sleep(2)
    
    print("\nSummary of saved images:")
    for meal, path in meal_to_image_path.items():
        print(f"{meal}: {path}")
