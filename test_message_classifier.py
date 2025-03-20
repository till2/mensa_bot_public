from message_classifier import process_user_message, classify_message_simple
from time_utils import parse_date_query, format_date_for_display
from ollama_mensa_bot_utils import setup_llm
from datetime import date

def test_simple_classification():
    """Test the simple rule-based classification without LLM"""
    test_cases = [
        ("/hilfe", "help", []),
        ("/menu", "menu", []),
        ("/menu morgen", "menu", ["morgen"]),
        ("/mensa Griebnitzsee", "mensa", ["Griebnitzsee"]),
        ("Was gibt es heute zu essen?", "menu", []),
        ("Zeig mir das Menü", "menu", []),
        ("Ich möchte zur Mensa Griebnitzsee wechseln", "mensa", []),
        ("Hilfe bitte", "help", []),
        ("Wie spät ist es?", "chat", []),
    ]
    
    for message, expected_command, expected_args in test_cases:
        command, args = process_user_message(message)
        print(f"Message: '{message}'")
        print(f"Expected: {expected_command}, {expected_args}")
        print(f"Got: {command}, {args}")
        print("---")

def test_date_parsing():
    """Test the date parsing functionality"""
    today = date.today().strftime("%Y-%m-%d")
    
    test_cases = [
        ("heute", today),
        ("morgen", None),  # Will be today + 1 day
        ("übermorgen", None),  # Will be today + 2 days
    ]
    
    for query, expected in test_cases:
        result = parse_date_query(query)
        print(f"Query: '{query}'")
        print(f"Result: {result}")
        if expected:
            print(f"Expected: {expected}")
        print(f"Formatted: {format_date_for_display(result)}")
        print("---")

def test_llm_classification():
    """Test the LLM-based classification"""
    # Only run this if you want to test with the LLM
    llm = setup_llm(model="phi3:3.8b", temperature=0.3)
    
    test_cases = [
        ("Was gibt es morgen in der Mensa zu essen?", "menu"),
        ("Zeig mir das Menü für Freitag", "menu"),
        ("Ich möchte zur Mensa Griebnitzsee wechseln", "mensa"),
        ("Kannst du mir sagen, was es übermorgen in der Mensa gibt?", "menu"),
        ("Wie ist das Wetter heute?", "chat"),
    ]
    
    for message, expected_command in test_cases:
        command, args = process_user_message(message, llm)
        print(f"Message: '{message}'")
        print(f"Expected: {expected_command}")
        print(f"Got: {command}, {args}")
        print("---")

if __name__ == "__main__":
    print("Testing simple classification...")
    test_simple_classification()
    
    print("\nTesting date parsing...")
    test_date_parsing()
    
    # Uncomment to test with LLM
    # print("\nTesting LLM classification...")
    # test_llm_classification() 