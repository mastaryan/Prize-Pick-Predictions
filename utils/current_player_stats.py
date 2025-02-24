"""
=============================================
* Uses the balldontlie API and searches for a specific
* player's current stats in different stat types.
=============================================
"""
from dotenv import load_dotenv
import requests
import os

load_dotenv()

def get_player_stats(full_name, current_season_year):
    # No API key needed for free tier
    n_a = "--"

    # Split the input string into words
    name_array = full_name.split()
    first_name = name_array[0]
    last_name = name_array[-1] if len(name_array) > 1 else ""

    # URL encoding for special characters (e.g., ć in Nurkić)
    import urllib.parse
    last_name_encoded = urllib.parse.quote(last_name)

    # Fetch player data without Authorization header
    url = f"https://api.balldontlie.io/v1/players?first_name={first_name}&last_name={last_name_encoded}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if not data["data"]:
            print(f"[🟡] No player found for {full_name}")
            return None, f"No player found for {full_name}"

        # Take the first matching player
        player = data["data"][0]
        fp_player_id = player["id"]
        fp_team_name = player["team"]["full_name"]

        # Fetch season averages
        player_url = f"https://api.balldontlie.io/v1/season_averages?season={current_season_year}&player_ids[]={fp_player_id}"
        player_response = requests.get(player_url)
        player_response.raise_for_status()
        player_stats_data = player_response.json()["data"]

        if not player_stats_data:
            print(f"[🟡] No stats available for {full_name} in {current_season_year}")
            return None, f"No stats available for {full_name} in {current_season_year}"

        player_stats = player_stats_data[0]
        fp_ftm = round(player_stats.get("ftm", n_a), 5)
        fp_points = round(player_stats.get("pts", n_a), 5)
        fp_rebounds = round(player_stats.get("reb", n_a), 5)
        fp_assists = round(player_stats.get("ast", n_a), 5)

        # Calculate combined stats, handling n_a cases
        fp_points_rebounds = round(fp_points + fp_rebounds, 5) if fp_points != n_a and fp_rebounds != n_a else n_a
        fp_points_assists = round(fp_points + fp_assists, 5) if fp_points != n_a and fp_assists != n_a else n_a
        fp_points_rebounds_assists = round(fp_points + fp_rebounds + fp_assists, 5) if (
            fp_points != n_a and fp_rebounds != n_a and fp_assists != n_a) else n_a

        return (
            player_stats,
            fp_player_id,
            fp_team_name,
            fp_points,
            fp_rebounds,
            fp_assists,
            fp_ftm,
            fp_points_rebounds,
            fp_points_assists,
            fp_points_rebounds_assists
        )
    except requests.exceptions.RequestException as e:
        print(f"[🔴] Error fetching player stats for {full_name}: {e}")
        return None, f"Error fetching player stats for {full_name}: {e}"