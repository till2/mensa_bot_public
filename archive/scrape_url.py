import requests
from bs4 import BeautifulSoup

class Element:
    def __init__(self, num: int, element_type: str, url: str, text: str):
        self.num = num
        self.type = element_type
        self.url = url
        self.text = text
    
    def __str__(self):
        if self.type == "link":
            return f"{self.num}. URL: {self.url}, Text: {self.text}"
        return f"Type: {self.type}, URL: {self.url}, Text: {self.text}"
    
    def __repr__(self):
        return self.__str__()

def extract_clickable_elements(url: str):
    """
    Fetches HTML from the provided URL and extracts clickable elements:
    - <a> tags with href attributes (links)
    - <button> tags
    - <input> tags of type 'button' or 'submit'
    - Other elements with an onclick attribute (potentially clickable)
    
    Parameters:
        url (str): The URL of the website to parse.
        
    Returns:
        List of Element objects describing each clickable element.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print("Error fetching URL:", e)
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    clickable_elements = []
    url_text_map = {}  # Dictionary to track URLs and their associated texts

    # Extract all <a> tags with href attribute (links)
    for a in soup.find_all('a', href=True):
        href = a.get('href')
        text = a.get_text(strip=True)
        
        # If URL already exists, keep the one with longer text
        if href in url_text_map:
            if len(text) > len(url_text_map[href][2]):
                url_text_map[href] = ("link", href, text)
        else:
            url_text_map[href] = ("link", href, text)
    
    # Add unique URLs to clickable_elements with numbering
    for i, (url, details) in enumerate(url_text_map.items(), 1):
        elem_type, href, text = details
        clickable_elements.append(Element(i, elem_type, href, text))
    
    # Extract <button> tags (buttons)
    for button in soup.find_all('button'):
        text = button.get_text(strip=True)
        onclick = button.get('onclick')
        clickable_elements.append(Element(0, "button", onclick or "", text))
    
    # Extract <input> elements of type 'button' or 'submit'
    for inp in soup.find_all('input', {'type': lambda t: t and t.lower() in ['button', 'submit']}):
        value = inp.get('value', '').strip()
        onclick = inp.get('onclick')
        clickable_elements.append(Element(0, "input", onclick or "", value))
    
    # Optionally, extract any other elements with an 'onclick' attribute
    for elem in soup.find_all(attrs={"onclick": True}):
        if elem.name not in ['a', 'button', 'input']:
            text = elem.get_text(strip=True)
            onclick = elem.get('onclick')
            clickable_elements.append(Element(0, "onclick", onclick or "", text))
    
    return clickable_elements

if __name__ == "__main__":
    url = "https://till2.github.io/"
    elements = extract_clickable_elements(url)
    
    for elem in elements:
        print(elem)
