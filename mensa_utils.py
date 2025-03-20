from openmensa import OpenMensa

def get_mensa_id(location: str) -> int:
    """Get the OpenMensa ID for a given mensa location."""
    mensa_to_id = {
        "Kiepenheuerallee": 57,
        "Griebnitzsee": 62,
    }
    return mensa_to_id[location]


def get_canteen_name(mensa_id: int) -> str:
    """Get the name of the canteen for a given mensa ID."""
    canteen_info = OpenMensa.get_canteen(mensa_id)
    return canteen_info["name"]


def is_canteen_closed(mensa_id: int, date: str) -> bool:
    """Check if the canteen is closed on a specific date."""
    for day in OpenMensa.get_canteen_days(mensa_id):
        if day["date"] == date:
            return day["closed"]
    return True  # Return True if date not found


def get_meals(mensa_id: int, date: str, excluded_categories=None) -> list:
    """
    Get meals for a specific date and mensa ID.
    Returns a list of tuples (category, name, price).
    """
    if excluded_categories is None:
        excluded_categories = ["Salattheke", "Dessert"]
    
    try:
        meals = OpenMensa.get_meals_by_day(mensa_id, date)
        filtered_meals = []
        
        for meal in meals:
            if any(excluded in meal["category"] for excluded in excluded_categories):
                continue
            filtered_meals.append((
                meal["category"],
                meal["name"],
                meal["prices"]["students"]
            ))
        return filtered_meals
    except Exception as e:
        return []


def print_daily_menu(location: str, date: str):
    """Print the daily menu for a specific mensa location and date."""
    mensa_id = get_mensa_id(location)
    print(get_canteen_name(mensa_id))
    
    if is_canteen_closed(mensa_id, date):
        print(f"Die Mensa ist heute geschlossen.")
        return
    
    meals = get_meals(mensa_id, date)
    if not meals:
        print(f"Keine Gerichte für den {date} verfügbar")
        return
        
    print(f"Gerichte am {date}:")
    for category, name, price in meals:
        print(f"{category}: {name} ({price:.2f}€)")

if __name__ == "__main__":
    print_daily_menu("Kiepenheuerallee", "2025-03-10")