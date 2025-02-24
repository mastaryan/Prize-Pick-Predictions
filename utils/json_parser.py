""" =============================================
* This module takes in two json files, and
* cleans/extracts only relevant information
* and formats it into the other json file
============================================= """

import json

def parse_json_file(pre_json, post_json):
    # Read the pre_json file
    try:
        with open(pre_json, "r") as file:
            data = json.load(file)
        print(f"[🟢] Successfully loaded {pre_json}")
    except Exception as e:
        print(f"[🔴] Error loading {pre_json}: {e}")
        return {}

    # Debug: Check included data
    included_data = data.get('included', [])
    print(f"Number of included items: {len(included_data)}")

    # Loop through included data to get player info
    results = {}
    for item in included_data:
        if item.get('type') == 'new_player':
            player_id = item.get('id')
            player_name = item.get('attributes', {}).get('name')
            if player_id and player_name:
                results[player_id] = {
                    'name': player_name,
                    'opposing_team_abv': None,
                    'strike_values': [],
                    'attributes': item.get('attributes', {})  # Store all attributes safely
                }

    # Debug: Report parsed players
    print(f"Number of players parsed: {len(results)}")
    if results:
        sample_player_id = list(results.keys())[0]
        print(f"Sample player data: {results[sample_player_id]}")

    # Loop through projection data to add stats
    for projection in data.get('data', []):
        if projection.get('type') == 'projection':
            player_id = projection.get('relationships', {}).get('new_player', {}).get('data', {}).get('id')
            if player_id in results:
                stat_type = projection.get('attributes', {}).get('stat_type')
                line_score = projection.get('attributes', {}).get('line_score')
                opposing_team = projection.get('attributes', {}).get('description')
                if stat_type and line_score:
                    results[player_id]['strike_values'].append({
                        'stat_type': stat_type,
                        'line_score': line_score
                    })
                results[player_id]['opposing_team_abv'] = opposing_team

    # Write results to post_json
    try:
        with open(post_json, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"[🟢] Successfully wrote parsed data to {post_json}")
    except Exception as e:
        print(f"[🔴] Error writing to {post_json}: {e}")

    return results

if __name__ == "__main__":
    # For testing
    parse_json_file("json files/pre_formatted_projections.json", "json files/post_formatted_projections.json")