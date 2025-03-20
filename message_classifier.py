from langchain.schema import HumanMessage, SystemMessage
import re
from time_utils import parse_date_query

# Command types
COMMAND_HELP = "help"
COMMAND_MENU = "menu"
COMMAND_MENSA = "mensa"
COMMAND_CHAT = "chat"
COMMAND_SETTINGS = "settings"
COMMAND_RESTART = "restart"
COMMAND_UNKNOWN = "unknown"

class MessageIntent:
    def __init__(self, command_type, args=None, date_str=None, mensa_location=None):
        self.command_type = command_type
        self.args = args or []
        self.date_str = date_str
        self.mensa_location = mensa_location
    
    def __str__(self):
        return f"Intent: {self.command_type}, Args: {self.args}, Date: {self.date_str}, Mensa: {self.mensa_location}"

def classify_message_simple(message_text):
    """
    Simple rule-based classification of user messages.
    
    Args:
        message_text (str): The user's message
        
    Returns:
        MessageIntent: The classified intent
    """
    # Check for direct commands first
    if message_text.startswith('/'):
        command = message_text.split()[0][1:].lower()
        args = message_text.split()[1:] if len(message_text.split()) > 1 else []
        
        if command in ["start", "hilfe", "help"]:
            return MessageIntent(COMMAND_HELP)
        elif command in ["menu", "menü"]:
            return MessageIntent(COMMAND_MENU, args)
        elif command in ["mensa"]:
            return MessageIntent(COMMAND_MENSA, args)
        elif command in ["chat"]:
            return MessageIntent(COMMAND_CHAT)
        elif command in ["einstellungen", "settings"]:
            return MessageIntent(COMMAND_SETTINGS)
        elif command in ["neustart", "restart"]:
            return MessageIntent(COMMAND_RESTART)
        else:
            return MessageIntent(COMMAND_UNKNOWN)
    
    # Simple pattern matching for common queries
    message_lower = message_text.lower()
    
    # Help patterns
    if re.search(r'\b(hilfe|befehle|kommandos|help|commands)\b', message_lower):
        return MessageIntent(COMMAND_HELP)
    
    # Menu patterns
    menu_patterns = [
        r'\b(menü|menu|essen|speiseplan|mahlzeit|gerichte)\b',
        r'\b(was gibt es|was gibt\'s)\b'
    ]
    
    for pattern in menu_patterns:
        if re.search(pattern, message_lower):
            return MessageIntent(COMMAND_MENU)
    
    # Mensa patterns
    mensa_patterns = [
        r'\b(mensa|kantine)\s+(?:wechseln|ändern|einstellen|setzen)\b',
        r'\b(wechsle|ändere)\s+(?:die|meine)?\s*mensa\b'
    ]
    
    for pattern in mensa_patterns:
        if re.search(pattern, message_lower):
            # Try to extract mensa location
            locations = ["kiepenheuerallee", "griebnitzsee"]
            for location in locations:
                if location in message_lower:
                    return MessageIntent(COMMAND_MENSA, mensa_location=location)
            return MessageIntent(COMMAND_MENSA)
    
    # Settings patterns
    if re.search(r'\b(einstellungen|settings|konfiguration|config)\b', message_lower):
        return MessageIntent(COMMAND_SETTINGS)
    
    # Restart patterns
    if re.search(r'\b(neustart|restart|reset|zurücksetzen)\b', message_lower):
        return MessageIntent(COMMAND_RESTART)
    
    # Default to chat for anything else
    return MessageIntent(COMMAND_CHAT)

def classify_message_with_llm(message_text, llm):
    """
    Use LLM to classify user message intent.
    
    Args:
        message_text (str): The user's message
        llm: LLM instance to use for classification
        
    Returns:
        MessageIntent: The classified intent
    """
    system_prompt = """
    You are a helpful assistant that classifies user messages into intents.
    Analyze the user's message and determine which command they want to use.
    
    Available commands:
    - help: User wants help or information about available commands
    - menu: User wants to see the menu (possibly for a specific date)
    - mensa: User wants to change their preferred mensa location
    - chat: User just wants to chat or ask a general question
    - settings: User wants to change settings
    - restart: User wants to restart or reset the conversation
    
    Respond with a JSON object containing:
    {
        "command": "one of [help, menu, mensa, chat, settings, restart]",
        "date": "YYYY-MM-DD if a date is mentioned, otherwise null",
        "mensa_location": "location name if mentioned (correct to valid names: "Kiepenheuerallee", "Griebnitzsee"), otherwise null"
    }
    
    Only include the JSON in your response, nothing else.
    """
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Classify this message: '{message_text}'")
    ]
    
    try:
        response = llm.invoke(messages).content.strip()
        
        # Extract JSON from response
        import json
        import re
        
        # Find JSON pattern in the response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            result = json.loads(json_str)
            
            command = result.get("command", COMMAND_UNKNOWN)
            date_str = result.get("date")
            mensa_location = result.get("mensa_location")
            
            return MessageIntent(command, date_str=date_str, mensa_location=mensa_location)
    except Exception as e:
        print(f"Error in LLM classification: {e}")
    
    # Fallback to simple classification
    return classify_message_simple(message_text)

def process_user_message(message_text, llm=None):
    """
    Process a user message to determine intent and extract relevant information.
    
    Args:
        message_text (str): The user's message
        llm: Optional LLM instance for advanced processing
        
    Returns:
        tuple: (command, args) where command is the command to execute and args are the arguments
    """
    # First try simple classification
    intent = classify_message_simple(message_text)
    
    # If we have an LLM and the intent is not clear, use the LLM
    if llm and intent.command_type == COMMAND_CHAT:
        # Check if this might be a menu request with a date
        if re.search(r'\b(menü|menu|essen|speiseplan|mahlzeit|gerichte)\b', message_text.lower()):
            # Try to extract a date
            date_str = parse_date_query(message_text, llm)
            if date_str:
                intent = MessageIntent(COMMAND_MENU, date_str=date_str)
        else:
            # Use LLM for full classification
            intent = classify_message_with_llm(message_text, llm)
    
    # Process the intent to return command and args
    if intent.command_type == COMMAND_MENU:
        # If we have a date from intent, use it
        if intent.date_str:
            return "menu", [intent.date_str]
        # Otherwise, try to extract date from message
        elif llm:
            date_str = parse_date_query(message_text, llm)
            return "menu", [date_str]
        # If no date and no LLM, return as is
        else:
            return "menu", intent.args
    
    elif intent.command_type == COMMAND_MENSA:
        if intent.mensa_location:
            return "mensa", [intent.mensa_location]
        else:
            # Try to extract mensa location from args or message
            locations = ["kiepenheuerallee", "griebnitzsee"]
            for location in locations:
                if location in message_text.lower():
                    return "mensa", [location]
            return "mensa", intent.args
    
    # For other commands, just return the command type and args
    return intent.command_type, intent.args 