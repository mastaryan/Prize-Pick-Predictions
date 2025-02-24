import time
from utils.json_parser import parse_json_file
from utils.bet_recommendation import predict
from utils.current_player_stats import get_player_stats
import requests
from utils.calculate_elo import start_calculating, sort_and_print
from utils.get_all_matches import get_all_matches
from utils.json_functions import wipe_json_files, open_or_create_json
import json
from dotenv import load_dotenv
import os

load_dotenv()

json_dir_location = "json files"
pre_json = "json files/pre_formatted_projections.json"
post_json = "json files/post_formatted_projections.json"
points_json = "json files/points.json"
assists_json = "json files/assists.json"
rebounds_json = "json files/rebounds.json"
points_assists_json = "json files/points_assists.json"
points_rebounds_json = "json files/points_rebounds.json"
points_assists_rebounds_json = "json files/points_assists_rebounds.json"
season_matches_json = "json files/match_results.json"
team_elos_json = "json files/team_elos.json"

wipe_json_files(json_dir_location)

current_season_year = 2024
api_key = os.getenv("BALL_DONT_LIE_API_KEY")
headers = {"Authorization": api_key} if api_key else {}

try:
    get_all_matches(season_matches_json, current_season_year, headers=headers)
    print(f"[🟢] Successfully fetched matches for {current_season_year} season.")
except Exception as e:
    print(f"[🔴] Failed to fetch matches: {e}. Proceeding with existing data.")

start_calculating(season_matches_json, team_elos_json)
sort_and_print(team_elos_json)

url = 'https://api.prizepicks.com/projections?league_id=7'
headers_prizepicks = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json"
}
try:
    response = requests.get(url, headers=headers_prizepicks)
    response.raise_for_status()
    json_data = response.json()
    with open(pre_json, 'w', encoding='utf-8') as json_file:
        json.dump(json_data, json_file, indent=2)
    print(f"[🟢] Successfully pulled and saved PrizePicks data to {pre_json}")
    print(f"Number of projections: {len(json_data.get('data', []))}")
    if json_data.get('included'):
        print(f"Sample player attributes: {json_data['included'][0].get('attributes', {})}")
except requests.exceptions.RequestException as e:
    print(f"[🔴] Error fetching PrizePicks data: {e}")
    json_data = {}

try:
    data = parse_json_file(pre_json, post_json) or {}
    print(f"[🟢] Successfully parsed JSON data. Number of players: {len(data)}")
    if data:
        sample_player_id = list(data.keys())[0]
        print(f"Sample player data: {data[sample_player_id]}")
except Exception as e:
    print(f"[🔴] Error parsing JSON: {e}. Using empty data.")
    data = {}

num_players = len(data)
players_printed = 0
table = []
n_a = "--"

default_data = []
points_data = open_or_create_json(points_json, default_data)
assists_data = open_or_create_json(assists_json, default_data)
rebounds_data = open_or_create_json(rebounds_json, default_data)
points_assists_data = open_or_create_json(points_assists_json, default_data)
points_rebounds_data = open_or_create_json(points_rebounds_json, default_data)
points_assists_rebounds_data = open_or_create_json(points_assists_rebounds_json, default_data)

for idx, key in enumerate(data):
    name = data[key]['name']
    team_name = data[key]['attributes']['team_name']
    team_city_state = data[key]['attributes']['market']
    photo_link = data[key]['attributes'].get('image_url', n_a)  # Use .get() for safety
    player_position = data[key]['attributes']['position']

    points = rebounds = assists = turnovers = points_assists = points_rebounds = points_rebounds_assists = n_a

    for item in data[key].get('strike_values', []):
        stat_type = item.get('stat_type')
        if stat_type == 'Points':
            points = item['line_score']
        elif stat_type == 'Turnovers':
            turnovers = item['line_score']
        elif stat_type == 'Rebounds':
            rebounds = item['line_score']
        elif stat_type == 'Assists':
            assists = item['line_score']
        elif stat_type == 'Pts+Asts':
            points_assists = item['line_score']
        elif stat_type == 'Pts+Rebs':
            points_rebounds = item['line_score']
        elif stat_type == 'Pts+Rebs+Asts':
            points_rebounds_assists = item['line_score']

    player_name = name
    num_attempts = 1
    min_attempts, max_attempts = 1, 3

    # Default stats
    fp_player_stats = fp_player_id = fp_team_name = fp_points = fp_rebounds = fp_assists = fp_ftm = fp_points_rebounds = fp_points_assists = fp_points_rebounds_assists = n_a

    for i in range(min_attempts, max_attempts):
        num_attempts = i
        try:
            stats = get_player_stats(player_name, current_season_year)
            if stats:
                print(f"[🟢] Fetched stats for {player_name}")
                stats = list(stats) + [n_a] * (10 - len(stats))  # Pad with n_a
                fp_player_stats, fp_player_id, fp_team_name, fp_points, fp_rebounds, fp_assists, fp_ftm, fp_points_rebounds, fp_points_assists, fp_points_rebounds_assists = stats[:10]
                break
            else:
                print(f"[🟡] No stats found for {player_name}")
        except Exception as e:
            if i < max_attempts - 1:
                print(f"[🟡] Failed to load {player_name}, attempt {num_attempts}/{max_attempts-1}: {e}")
                time.sleep(i)
            else:
                print(f"[🔴] Final attempt failed for {player_name}: {e}")

    # Process data even if stats are partial
    recommendation_pts = predict(points, fp_points, n_a)
    recommendation_reb = predict(rebounds, fp_rebounds, n_a)
    recommendation_ast = predict(assists, fp_assists, n_a)
    recommendation_pts_ast = predict(points_assists, fp_points + fp_assists if fp_points != n_a and fp_assists != n_a else n_a, n_a)
    recommendation_pts_reb = predict(points_rebounds, fp_points + fp_rebounds if fp_points != n_a and fp_rebounds != n_a else n_a, n_a)
    recommendation_pts_ast_reb = predict(points_rebounds_assists, fp_points + fp_assists + fp_rebounds if fp_points != n_a and fp_assists != n_a and fp_rebounds != n_a else n_a, n_a)

    table.append(
        [idx + 1, name, team_name, points, fp_points, recommendation_pts, rebounds, fp_rebounds,
         recommendation_reb, assists, fp_assists, recommendation_ast, points_assists,
         points_rebounds, points_rebounds_assists])

    diff_pts = round(abs(float(fp_points) - float(points)), 5) if points != n_a and fp_points != n_a else n_a
    diff_reb = round(abs(float(fp_rebounds) - float(rebounds)), 5) if rebounds != n_a and fp_rebounds != n_a else n_a
    diff_assists = round(abs(float(fp_assists) - float(assists)), 5) if assists != n_a and fp_assists != n_a else n_a
    diff_pts_ast = round(abs((float(fp_points) + float(fp_assists)) - float(points_assists)), 5) if points_assists != n_a and fp_points != n_a and fp_assists != n_a else n_a
    diff_pts_reb = round(abs((float(fp_points) + float(fp_rebounds)) - float(points_rebounds)), 5) if points_rebounds != n_a and fp_points != n_a and fp_rebounds != n_a else n_a
    diff_pts_ast_reb = round(abs((float(fp_points) + float(fp_assists) + float(fp_rebounds)) - float(points_rebounds_assists)), 5) if points_rebounds_assists != n_a and fp_points != n_a and fp_assists != n_a and fp_rebounds != n_a else n_a

    if recommendation_pts != n_a:
        points_data.append({player_name: {"general": {"player_id": fp_player_id, "team_name": team_name, "team_market": team_city_state, "picture_link": photo_link, "player_position": player_position}, "stats": {"type": "points", "strike_value": points, "predicted_value": fp_points, "bet_recommendation": recommendation_pts, "difference": diff_pts}}})
    if recommendation_ast != n_a:
        assists_data.append({player_name: {"general": {"player_id": fp_player_id, "team_name": team_name, "team_market": team_city_state, "picture_link": photo_link, "player_position": player_position}, "stats": {"type": "assists", "strike_value": assists, "predicted_value": fp_assists, "bet_recommendation": recommendation_ast, "difference": diff_assists}}})
    if recommendation_reb != n_a:
        rebounds_data.append({player_name: {"general": {"player_id": fp_player_id, "team_name": team_name, "team_market": team_city_state, "picture_link": photo_link, "player_position": player_position}, "stats": {"type": "rebounds", "strike_value": rebounds, "predicted_value": fp_rebounds, "bet_recommendation": recommendation_reb, "difference": diff_reb}}})
    if recommendation_pts_ast != n_a:
        points_assists_data.append({player_name: {"general": {"player_id": fp_player_id, "team_name": team_name, "team_market": team_city_state, "picture_link": photo_link, "player_position": player_position}, "stats": {"type": "pts+ast", "strike_value": points_assists, "predicted_value": fp_points + fp_assists if fp_points != n_a and fp_assists != n_a else n_a, "bet_recommendation": recommendation_pts_ast, "difference": diff_pts_ast}}})
    if recommendation_pts_reb != n_a:
        points_rebounds_data.append({player_name: {"general": {"player_id": fp_player_id, "team_name": team_name, "team_market": team_city_state, "picture_link": photo_link, "player_position": player_position}, "stats": {"type": "pts+rebs", "strike_value": points_rebounds, "predicted_value": fp_points + fp_rebounds if fp_points != n_a and fp_rebounds != n_a else n_a, "bet_recommendation": recommendation_pts_reb, "difference": diff_pts_reb}}})
    if recommendation_pts_ast_reb != n_a:
        points_assists_rebounds_data.append({player_name: {"general": {"player_id": fp_player_id, "team_name": team_name, "team_market": team_city_state, "picture_link": photo_link, "player_position": player_position}, "stats": {"type": "pts+rebs+asts", "strike_value": points_rebounds_assists, "predicted_value": fp_points + fp_assists + fp_rebounds if fp_points != n_a and fp_assists != n_a and fp_rebounds != n_a else n_a, "bet_recommendation": recommendation_pts_ast_reb, "difference": diff_pts_ast_reb}}})

    with open(points_json, 'w') as f_points:
        json.dump(points_data, f_points, indent=2)
    with open(assists_json, 'w') as f_assists:
        json.dump(assists_data, f_assists, indent=2)
    with open(rebounds_json, 'w') as f_rebounds:
        json.dump(rebounds_data, f_rebounds, indent=2)
    with open(points_assists_json, 'w') as f_points_assists:
        json.dump(points_assists_data, f_points_assists, indent=2)
    with open(points_rebounds_json, 'w') as f_points_rebounds:
        json.dump(points_rebounds_data, f_points_rebounds, indent=2)
    with open(points_assists_rebounds_json, 'w') as f_points_assists_rebounds:
        json.dump(points_assists_rebounds_data, f_points_assists_rebounds, indent=2)

    players_printed += 1
    players_percentage = round((players_printed / num_players) * 100) if num_players > 0 else 0
    print(f"[🟢] Load Status: Successful  Player: {player_name:<25} Attempts: {num_attempts}/{max_attempts-1} ({players_printed:0>2}/{num_players} | {players_percentage:0>2}%)")

    time.sleep(1.25)

print(f"Points data: {len(points_data)} entries")
print(f"Assists data: {len(assists_data)} entries")
print(f"Rebounds data: {len(rebounds_data)} entries")
print(f"Points + Assists data: {len(points_assists_data)} entries")
print(f"Points + Rebounds data: {len(points_rebounds_data)} entries")
print(f"Points + Rebounds + Assists data: {len(points_assists_rebounds_data)} entries")

num_na_stats = sum(1 for row in table if n_a in row)
print(f"\n{num_na_stats} players have at least one missing stat.")
print(f"A total of {num_players} player objects in json file.")
print(f"{players_printed}/{num_players} were printed out in table format.\n\n")

from flask import Flask, render_template, request
import json

app = Flask(__name__)

@app.route('/')
def index():
    data_source = request.args.get('data_source', 'points')
    try:
        if data_source == 'points':
            with open('json files/points.json') as f:
                data = json.load(f)
            print(f"Loaded {len(data)} points entries for Flask")
        elif data_source == 'rebounds':
            with open('json files/rebounds.json') as f:
                data = json.load(f)
            print(f"Loaded {len(data)} rebounds entries for Flask")
        elif data_source == 'assists':
            with open('json files/assists.json') as f:
                data = json.load(f)
            print(f"Loaded {len(data)} assists entries for Flask")
        elif data_source == 'pts_asts':
            with open('json files/points_assists.json') as f:
                data = json.load(f)
            print(f"Loaded {len(data)} pts+asts entries for Flask")
        elif data_source == 'pts_rebs':
            with open('json files/points_rebounds.json') as f:
                data = json.load(f)
            print(f"Loaded {len(data)} pts+rebs entries for Flask")
        elif data_source == 'pts_rebs_asts':
            with open('json files/points_assists_rebounds.json') as f:
                data = json.load(f)
            print(f"Loaded {len(data)} pts+rebs+asts entries for Flask")
    except Exception as e:
        print(f"[🔴] Error loading Flask data: {e}")
        data = []
    return render_template('index.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)