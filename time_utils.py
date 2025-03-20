from datetime import datetime, date, timedelta
from langchain.schema import HumanMessage, SystemMessage
import re

def parse_date_query(query, llm=None):
    """
    Parse a natural language date query and return a date string in YYYY-MM-DD format.
    
    Args:
        query (str): Natural language query like "menü für morgen" or "essen am Freitag"
        llm: LLM instance to use for parsing
        
    Returns:
        str: Date string in YYYY-MM-DD format
    """
    today = date.today()
    
    # Simple pattern matching for common cases
    if re.search(r'\b(heute|today)\b', query, re.IGNORECASE):
        return today.strftime("%Y-%m-%d")
    
    if re.search(r'\b(morgen|tomorrow)\b', query, re.IGNORECASE):
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    
    if re.search(r'\b(übermorgen|day after tomorrow)\b', query, re.IGNORECASE):
        return (today + timedelta(days=2)).strftime("%Y-%m-%d")
    
    # Direct weekday matching
    weekday_patterns = {
        'montag': 0,
        'dienstag': 1,
        'mittwoch': 2,
        'donnerstag': 3,
        'freitag': 4,
        'samstag': 5,
        'sonntag': 6,
        'monday': 0,
        'tuesday': 1,
        'wednesday': 2,
        'thursday': 3,
        'friday': 4,
        'saturday': 5,
        'sunday': 6
    }
    
    query_lower = query.lower()
    for day_name, day_num in weekday_patterns.items():
        if day_name in query_lower:
            # Calculate days until the next occurrence of this weekday
            days_ahead = day_num - today.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            target_date = today + timedelta(days=days_ahead)
            return target_date.strftime("%Y-%m-%d")
    
    # For more complex queries, use the LLM
    if llm:
        return parse_date_with_llm(query, llm)
    
    # Default to today if no date is recognized
    return today.strftime("%Y-%m-%d")

def parse_date_with_llm(query, llm):
    """
    Use LLM to parse a date from natural language.
    
    Args:
        query (str): Natural language query
        llm: LLM instance to use for parsing
        
    Returns:
        str: Date string in YYYY-MM-DD format
    """
    today = date.today()
    
    system_prompt = """
    You are a helpful assistant that extracts date information from text.
    Extract the date mentioned in the user's query relative to today.
    Today's date is {today}.
    
    Important rules:
    1. ALWAYS use the current year ({current_year}) unless explicitly specified otherwise
    2. For weekdays, find the NEXT occurrence of that day
    3. For relative days (e.g., "morgen", "übermorgen", "tomorrow"), calculate from today
    4. For specific dates (e.g., "23. Mai"), use the current or next occurrence
    
    Respond ONLY with the date in YYYY-MM-DD format. If no date is mentioned, respond with today's date.
    """.format(
        today=today.strftime("%Y-%m-%d"),
        current_year=today.year
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Extract the date from: '{query}'")
    ]
    
    try:
        response = llm.invoke(messages).content.strip()
        
        # Validate the response is in YYYY-MM-DD format
        parsed_date = datetime.strptime(response, "%Y-%m-%d").date()
        
        # If the returned date is in the past, move it to next year
        if parsed_date < today:
            parsed_date = parsed_date.replace(year=today.year + 1)
            
        return parsed_date.strftime("%Y-%m-%d")
    except (ValueError, Exception) as e:
        print(f"Error parsing date with LLM: {e}")
        # If parsing fails, return today's date
        return today.strftime("%Y-%m-%d")

def get_weekday_name(date_str):
    """
    Get the weekday name for a given date string.
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        
    Returns:
        str: Weekday name in German
    """
    weekday_names = {
        0: "Montag",
        1: "Dienstag",
        2: "Mittwoch",
        3: "Donnerstag",
        4: "Freitag",
        5: "Samstag",
        6: "Sonntag"
    }
    
    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    return weekday_names[date_obj.weekday()]

def format_date_for_display(date_str):
    """
    Format a date string for display in German format.
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        
    Returns:
        str: Formatted date string like "Montag, 10.03.2025"
    """
    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    weekday = get_weekday_name(date_str)
    return f"{weekday}, {date_obj.strftime('%d.%m.%Y')}" 