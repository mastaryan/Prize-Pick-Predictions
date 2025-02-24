import requests
import json
import time

def fetch_and_save_data(page_number, current_season_year, headers=None):
    if headers is None:
        headers = {}
    url = f"https://api.balldontlie.io/v1/games?seasons[]={current_season_year}&per_page=100&page={page_number}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        return result.get("data", []), result.get("meta", {}).get("next_page")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from page {page_number}: {e}")
        return None, None

def sort_data_by_date(data):
    return sorted(data, key=lambda x: x.get("date", ""))

def get_all_matches(write_file, current_season_year, headers=None):
    all_data = []
    current_page = 1

    while True:
        page_data, next_page = fetch_and_save_data(current_page, current_season_year, headers=headers)
        
        if not page_data:
            break
        
        all_data.extend(page_data)
        
        if next_page is None:
            break
        
        current_page += 1
        time.sleep(1)  # Respect rate limits (60 requests/minute)

    # Filter for "Final" status and sort
    final_data = [entry for entry in all_data if entry.get("status") == "Final"]
    sorted_final_data = sort_data_by_date(final_data)

    with open(write_file, "w") as json_file:
        json.dump(sorted_final_data, json_file, indent=2)

    print(f"[🟢] Successfully fetched {len(sorted_final_data)} final games for {current_season_year} season.")
    return None