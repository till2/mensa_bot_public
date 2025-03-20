import requests

response = requests.get('https://openmensa.org/api/v2/canteens')
canteens = response.json()

# Filter for canteens in Potsdam and Berlin
filtered_canteens = [canteen for canteen in canteens if "Potsdam" in canteen['city'] or "Berlin" in canteen["city"]]

# Print the filtered canteens
for canteen in filtered_canteens:
    print(f"{canteen['id']}: {canteen['name']} in {canteen['city']}")


# 57: Mensa Kiepenheuerallee in Potsdam
# 62: Mensa Griebnitzsee in Potsdam
