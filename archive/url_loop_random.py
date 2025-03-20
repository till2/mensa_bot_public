import random
import time
from urllib.parse import urljoin
from scrape_url import extract_clickable_elements

def is_valid_url(url: str) -> bool:
    """Check if URL is valid for crawling (internal or certain allowed external)"""
    return (
        url.startswith(('http://', 'https://')) and
        not url.startswith('mailto:') and
        'till2.github.io' in url  # Only crawl within the blog
    )

def random_crawl(start_url: str, delay: float = 1.0, max_visits: int = 10):
    visited_urls = set()
    current_url = start_url
    visit_count = 0

    while visit_count < max_visits:
        print(f"\nVisiting ({visit_count + 1}/{max_visits}): {current_url}")
        visited_urls.add(current_url)
        
        # Get all elements from the current page
        elements = extract_clickable_elements(current_url)
        
        # Filter for valid URLs we haven't visited
        valid_elements = [
            elem for elem in elements 
            if is_valid_url(urljoin(current_url, elem.url)) 
            and urljoin(current_url, elem.url) not in visited_urls
        ]
        
        if not valid_elements:
            print("No more unvisited links found. Ending crawl.")
            break
            
        # Select random element and get its absolute URL
        next_element = random.choice(valid_elements)
        next_url = urljoin(current_url, next_element.url)
        
        print(f"Selected: {next_element.text} ({next_url})")
        
        # Update for next iteration
        current_url = next_url
        visit_count += 1
        
        # Be nice to the server
        time.sleep(delay)

if __name__ == "__main__":
    start_url = "https://till2.github.io/"
    random_crawl(start_url, delay=0.0, max_visits=5)