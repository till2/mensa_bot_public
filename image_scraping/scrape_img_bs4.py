import requests
from bs4 import BeautifulSoup
import os
import time
from urllib.parse import quote
from io import BytesIO
from PIL import Image

def extract_meal_image(meal_name):
    """
    Searches for an image of a meal using DuckDuckGo Images and returns the image object.
    
    Parameters:
        meal_name (str): Name of the meal to search for
        
    Returns:
        PIL.Image.Image: Image object if found, None otherwise
    """
    try:
        print(f"Searching for image of: {meal_name}")
        
        # Format the search query - add "food" to get better results
        search_query = quote(f"{meal_name} food dish")
        
        # Use DuckDuckGo instead of Google as it's easier to scrape
        search_url = f"https://duckduckgo.com/?q={search_query}&iax=images&ia=images"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Make the request
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for image data in the page source
        # DuckDuckGo includes image data in vqd attributes
        scripts = soup.find_all('script')
        img_url = None
        
        # Try to find image URLs in script tags
        for script in scripts:
            if script.string and 'vqd' in str(script.string):
                # Extract the vqd value
                vqd_start = script.string.find('vqd=')
                if vqd_start != -1:
                    vqd_start += 4
                    vqd_end = script.string.find("'", vqd_start)
                    if vqd_end != -1:
                        vqd = script.string[vqd_start:vqd_end]
                        
                        # Now make a request to the DuckDuckGo image API
                        api_url = f"https://duckduckgo.com/i.js?q={search_query}&vqd={vqd}&o=json"
                        api_response = requests.get(api_url, headers=headers)
                        
                        if api_response.status_code == 200:
                            try:
                                image_data = api_response.json()
                                if 'results' in image_data and len(image_data['results']) > 0:
                                    img_url = image_data['results'][0]['image']
                                    break
                            except:
                                pass
        
        if img_url:
            # Download and return the image
            img_response = requests.get(img_url, headers=headers)
            img = Image.open(BytesIO(img_response.content))
            return img
        else:
            print(f"  No valid image URL found for {meal_name}")
            return None
            
    except Exception as e:
        print(f"  Error finding image for {meal_name}: {str(e)}")
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
        img = extract_meal_image(meal_name)
        if img:
            # Create a safe filename
            safe_filename = "".join(c if c.isalnum() else "_" for c in meal_name)
            img_path = os.path.join(images_dir, f"{safe_filename}.jpg")
            
            # Save the image
            img.save(img_path)
            print(f"  Image saved to {img_path}")
            meal_to_image_path[meal_name] = img_path
            
        # Be nice to the server with a small delay
        time.sleep(1)
    
    print("\nSummary of saved images:")
    for meal, path in meal_to_image_path.items():
        print(f"{meal}: {path}")