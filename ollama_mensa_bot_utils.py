from openmensa import OpenMensa
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
import json
import re
import mensa_utils
from datetime import date
from dotenv import load_dotenv
import os

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Define system prompt for meal classification
MEAL_CLASSIFICATION_PROMPT = """You are a helpful assistant that classifies meals as vegetarian or non-vegetarian.
Analyze the meal name and ingredients to determine if it's vegetarian.
Respond in JSON format as follows:
{
    "type": "vegetarian" or "non-vegetarian",
    "emojis": ["emoji1", "emoji2", "emoji3"]  # 1-3 fitting food emojis
}

Note that the input text is German. But the output should be in English.
Choose appropriate emojis based on the ingredients or type of dish.

Example 1:
Input: "Spaghetti Bolognese"
Output: {"type": "non-vegetarian", "emojis": ["🍝", "🥩"]}

Example 2:
Input: "Kartoffeln mit Spiegelei"
Output: {"type": "vegetarian", "emojis": ["🥔", "🍳"]}

Example 3:
Input: "Hamburger"
Output: {"type": "non-vegetarian", "emojis": ["🍔"]}
"""

def setup_llm(model="phi3:3.8b", temperature=0.3, num_predict=512):
    """Initialize and return the LLM with specified parameters"""
    # return ChatOllama(
    #     model=model,
    #     temperature=temperature,
    #     num_predict=num_predict,
    # )
    
    # return ChatGroq(
    #     model="llama-3.2-90b-vision-preview",
    #     temperature=temperature,
    #     api_key="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",
    # )
    
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=temperature,
        api_key=OPENAI_API_KEY,
    )

def classify_meal(meal_name, llm=None):
    """Use LLM to classify a meal as vegetarian or non-vegetarian"""
    if llm is None:
        llm = setup_llm()
        
    messages = [
        ("system", MEAL_CLASSIFICATION_PROMPT),
        ("human", f"Classify this meal as vegetarian or non-vegetarian: {meal_name}")
    ]
    
    try:
        response = llm.invoke(messages).content.strip()
        
        # Extract JSON object from response
        json_match = re.search(r'\{.*?\}', response, re.DOTALL)
        if not json_match:
            # Could not find JSON in response
            return "unknown", "🍽️"
            
        json_str = json_match.group()
        
        # Parse JSON and get classification
        try:
            result = json.loads(json_str)
            meal_type = result.get('type', '').lower()
            emojis = result.get('emojis', ['🍽️'])  # Default emoji if none provided
            emoji_str = ''.join(emojis)
            if meal_type in ['vegetarian', 'non-vegetarian']:
                return meal_type, emoji_str
            else:
                # Invalid meal type in response
                return "unknown", "🍽️"
        except json.JSONDecodeError as e:
            # Error parsing JSON response
            return "unknown", "🍽️"
            
    except Exception as e:
        # Error classifying meal
        return "unknown", "🍽️"

def get_mensa_meals(mensa_name, date_str, llm=None):
    """Get meals from a specific mensa on a specific date and classify them"""
    try:
        mensa_id = mensa_utils.get_mensa_id(mensa_name)
    except KeyError:
        return {"error": f"Unbekannte Mensa: {mensa_name}"}
    
    if mensa_utils.is_canteen_closed(mensa_id, date_str):
        return {"error": f"Die Mensa {mensa_name} ist am {date_str} geschlossen."}
    
    # Get meals and classify them
    try:
        meals = mensa_utils.get_meals(mensa_id, date_str)
        vegetarian_meals = {}
        non_vegetarian_meals = {}
        
        for category, name, price in meals:
            meal_info = f"{name} ({price:.2f}€)"
            
            # Classify the meal
            classification, emojis = classify_meal(name, llm)
            meal_info = f"{emojis} {meal_info}"
            
            if classification == "vegetarian":
                if category not in vegetarian_meals:
                    vegetarian_meals[category] = []
                vegetarian_meals[category].append(meal_info)
            else:
                if category not in non_vegetarian_meals:
                    non_vegetarian_meals[category] = []
                non_vegetarian_meals[category].append(meal_info)
        
        return {
            "vegetarian": vegetarian_meals,
            "non_vegetarian": non_vegetarian_meals
        }
    
    except Exception as e:
        return {"error": f"Gerichte für {date_str} konnten nicht abgerufen werden: {e}"}

def format_meals_output(meals_data):
    """Format the meals data into a readable string"""
    if "error" in meals_data:
        return meals_data["error"]
    
    output = []
    
    output.append("\n🥦 VEGETARISCHE GERICHTE")
    output.append("-" * 50)
    for category, meals in meals_data["vegetarian"].items():
        output.append(f"\n{category}:")
        for meal in meals:
            output.append(f"  • {meal}")
    
    output.append("\n🥩 NICHT-VEGETARISCHE GERICHTE")
    output.append("-" * 50)
    for category, meals in meals_data["non_vegetarian"].items():
        output.append(f"\n{category}:")
        for meal in meals:
            output.append(f"  • {meal}")
    
    return "\n".join(output)

def get_formatted_mensa_meals(mensa_name, date_str=None, llm=None):
    """Get and format meals for a specific mensa and date"""
    if date_str is None:
        date_str = date.today().strftime("%Y-%m-%d")
  
    header = f"\nGerichte in der Mensa {mensa_name} am {date_str}:"
    separator = "=" * 35
    
    meals_data = get_mensa_meals(mensa_name, date_str, llm)
    if "error" in meals_data:
        return f"{header}\n{separator}\n{meals_data['error']}"
    
    formatted_meals = format_meals_output(meals_data)
    return f"{header}\n{separator}{formatted_meals}"

if __name__ == "__main__":
    mensa_name = "Kiepenheuerallee"
    current_date = date.today().strftime("%Y-%m-%d")  # e.g. 2025-03-13
    # current_date = "2025-03-10"
    
    print(get_formatted_mensa_meals(mensa_name, current_date))
