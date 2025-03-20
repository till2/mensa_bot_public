from time_utils import parse_date_query, format_date_for_display
from datetime import date, datetime, timedelta

def test_weekday_parsing():
    """Test the weekday parsing functionality"""
    today = date.today()
    today_weekday = today.weekday()  # 0 = Monday, 1 = Tuesday, etc.
    
    # Test all weekdays
    weekdays = {
        "montag": 0,
        "dienstag": 1,
        "mittwoch": 2,
        "donnerstag": 3,
        "freitag": 4,
        "samstag": 5,
        "sonntag": 6
    }
    
    print(f"Today is {format_date_for_display(today.strftime('%Y-%m-%d'))}")
    
    for day_name, day_num in weekdays.items():
        # Calculate expected date
        days_ahead = day_num - today_weekday
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        expected_date = today + timedelta(days=days_ahead)
        expected_str = expected_date.strftime("%Y-%m-%d")
        
        # Test parsing
        result = parse_date_query(f"Menü für {day_name}")
        
        print(f"Query: 'Menü für {day_name}'")
        print(f"Expected: {expected_str} ({format_date_for_display(expected_str)})")
        print(f"Got: {result} ({format_date_for_display(result)})")
        print(f"Correct: {result == expected_str}")
        print("---")

def test_relative_days():
    """Test relative day parsing"""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    day_after_tomorrow = today + timedelta(days=2)
    
    test_cases = [
        ("heute", today.strftime("%Y-%m-%d")),
        ("menü heute", today.strftime("%Y-%m-%d")),
        ("morgen", tomorrow.strftime("%Y-%m-%d")),
        ("menü für morgen", tomorrow.strftime("%Y-%m-%d")),
        ("übermorgen", day_after_tomorrow.strftime("%Y-%m-%d")),
        ("essen übermorgen", day_after_tomorrow.strftime("%Y-%m-%d")),
    ]
    
    for query, expected in test_cases:
        result = parse_date_query(query)
        print(f"Query: '{query}'")
        print(f"Expected: {expected} ({format_date_for_display(expected)})")
        print(f"Got: {result} ({format_date_for_display(result)})")
        print(f"Correct: {result == expected}")
        print("---")

if __name__ == "__main__":
    print("Testing weekday parsing...")
    test_weekday_parsing()
    
    print("\nTesting relative days...")
    test_relative_days() 