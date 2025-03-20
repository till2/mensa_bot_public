import random
import time
from urllib.parse import urljoin
from scrape_url import extract_clickable_elements
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model = "phi3:3.8b",
    temperature = 0.7,
    num_predict = 256,
)

system_prompt = """You are a helpful assistant. You are given a list of clickable elements on a webpage. 
You need to select the most relevant element to click on. You should only click on elements that are relevant to the user's query. 
Output the number of the element you want to click on as $\boxed{number}$, where number is the number of the element in the list you want to click on."""

messages = [
    ("system", system_prompt),
]

def get_number(messages, num_attempts=3, verbose=False):
    for i in range(num_attempts):
        try:
            if verbose:
                print(f"Messages: {messages}")
            response = llm.invoke(messages).content
            if verbose:
                print(f"Response: {response}")
            # Filter out the $\boxed{number}$ part
            prefix, suffix = "\\boxed{", "}"
            number = int(response.split(prefix)[1].split(suffix)[0])
            return number
        except Exception as e:
            print(f"[attempt {i+1}/{num_attempts}] Error getting number: {e}")
            if verbose:
                print(f"Response: {response}")
            continue
    return 0

def is_valid_url(url: str) -> bool:
    """Check if URL is valid for crawling (internal or certain allowed external)"""
    return (
        url.startswith(('http://', 'https://')) and
        not url.startswith('mailto:') 
        # and 'till2.github.io' in url  # Only crawl within the blog
    )

def random_crawl(start_url: str, intent: str, delay: float = 1.0, max_visits: int = 10):
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
        # Re-index the elements
        for i, elem in enumerate(valid_elements):
            elem.num = i

        if not valid_elements:
            print("No more unvisited links found. Ending crawl.")
            break
           
        messages_with_elements = messages.copy() + [
            ("system", f"User intent: {intent}"),
            ("human", f"Here are the clickable elements (button, link, etc.) on the page: \n{valid_elements}")
        ]
        try:
            next_element = valid_elements[get_number(messages_with_elements)]
        except Exception as e:
            print(f"Error accessing list or getting number: {e}")
            next_element = random.choice(valid_elements)

        # Run LLM
        next_url = urljoin(current_url, next_element.url)
        print(f"Selected: {next_element.text} ({next_url})")
        
        # Update for next iteration
        current_url = next_url
        visit_count += 1
        
        # Be nice to the server
        time.sleep(delay)

if __name__ == "__main__":
    # start_url = "https://till2.github.io/"
    # intent = "i want to learn about RL"

    start_url = "https://gymnasium.farama.org/"
    intent = "want to learn about actor critics"
    random_crawl(start_url, intent, delay=0.0, max_visits=5)