import json
import math

def probability(rating1, rating2):
    """Calculate the expected probability of rating1 beating rating2."""
    return 1.0 / (1 + 1.0 * math.pow(10, (rating1 - rating2) / 400))

def elo_rating(rating_a, rating_b, k, d):
    """Update Elo ratings based on match outcome (d: 1 for home win, 0 for visitor win)."""
    # Home team gets a +100 advantage in expected probability
    pa = probability(rating_b + 100, rating_a) if d == 1 else probability(rating_b + 100, rating_a)
    pb = probability(rating_a, rating_b + 100) if d == 1 else probability(rating_a, rating_b + 100)

    rating_a = rating_a + k * (1 - pa) if d == 1 else rating_a + k * (0 - pa)
    rating_b = rating_b + k * (0 - pb) if d == 1 else rating_b + k * (1 - pb)

    return rating_a, rating_b

def update_elo(match, team_elos):
    """Update team Elo ratings and stats based on a single match."""
    home_team_id = match["home_team"]["id"]
    visitor_team_id = match["visitor_team"]["id"]

    # Initialize teams if not present
    home_team_elo, home_team_wins, home_team_losses, home_team_name, home_team_city, home_team_history = team_elos.get(
        home_team_id, (1500, 0, 0, match["home_team"]["name"], match["home_team"]["city"], [])
    )
    visitor_team_elo, visitor_team_wins, visitor_team_losses, visitor_team_name, visitor_team_city, visitor_team_history = team_elos.get(
        visitor_team_id, (1500, 0, 0, match["visitor_team"]["name"], match["visitor_team"]["city"], [])
    )

    # Determine result: 1 for home win, 0 for visitor win
    result = 1 if match["home_team_score"] > match["visitor_team_score"] else 0

    # Update Elo ratings
    home_team_elo, visitor_team_elo = elo_rating(home_team_elo, visitor_team_elo, 20, result)

    # Update wins/losses
    home_team_wins += result
    home_team_losses += 1 - result
    visitor_team_wins += 1 - result
    visitor_team_losses += result

    # Record match history with corrected 'loser' spelling
    home_team_history.append({
        "match_id": match["id"],
        "date": match["date"],
        "elo": home_team_elo,
        "result": "Win" if result == 1 else "Loss",
        "opposing_team": visitor_team_name,
        "scores": {"winner_score": match["home_team_score"], "loser_score": match["visitor_team_score"]}
    })
    visitor_team_history.append({
        "match_id": match["id"],
        "date": match["date"],
        "elo": visitor_team_elo,
        "result": "Win" if result == 0 else "Loss",
        "opposing_team": home_team_name,
        "scores": {"winner_score": match["visitor_team_score"], "loser_score": match["home_team_score"]}
    })

    # Update team_elos dictionary
    team_elos[home_team_id] = (home_team_elo, home_team_wins, home_team_losses, home_team_name, home_team_city, home_team_history)
    team_elos[visitor_team_id] = (visitor_team_elo, visitor_team_wins, visitor_team_losses, visitor_team_name, visitor_team_city, visitor_team_history)

    return team_elos

def sort_teams_by_elo(team_stats):
    """Sort teams by Elo rating in descending order."""
    return dict(sorted(team_stats.items(), key=lambda x: x[1]["elo"], reverse=True))

def print_team_stats(team_stats):
    """Print formatted team stats table."""
    print("{:<5} {:<35} {:<15} {:<8} {:<8} {:<15} {:<10}".format(
        "Idx", "Team", "Elo", "Wins", "Losses", "Total Games", "Win Rate"
    ))
    print("=" * 105)
    for index, (team_id, stats) in enumerate(team_stats.items(), 1):
        print("{:<5} {:<35} {:<15.2f} {:<8} {:<8} {:<15} {:<10.2f}".format(
            index,
            f"{stats['city']} {stats['team_name']}",
            stats['elo'],
            stats['wins'],
            stats['losses'],
            stats['total_games'],
            stats['win_rate']
        ))

def sort_and_print(elo_json):
    """Load, sort, and print team stats from JSON file."""
    try:
        with open(elo_json, "r") as file:
            team_stats = json.load(file)
        sorted_teams = sort_teams_by_elo(team_stats)
        print_team_stats(sorted_teams)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[🔴] Error loading or parsing {elo_json}: {e}")

def start_calculating(read_file, write_file):
    """Calculate Elo ratings and stats for all teams from match data."""
    try:
        with open(read_file, "r") as file:
            matches = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[🔴] Error reading {read_file}: {e}")
        return

    team_elos = {}

    for match in matches:
        team_elos = update_elo(match, team_elos)

    # Transform into team_stats format
    team_stats = {
        team_id: {
            "elo": elo,
            "wins": wins,
            "losses": losses,
            "total_games": wins + losses,
            "win_rate": wins / (wins + losses) * 100 if (wins + losses) > 0 else 0,
            "team_name": team_name,
            "city": city,
            "match_history": history
        }
        for team_id, (elo, wins, losses, team_name, city, history) in team_elos.items()
    }

    try:
        with open(write_file, "w") as file:
            json.dump(team_stats, file, indent=2)
        print(f"[🟢] Successfully calculated and saved {len(team_stats)} NBA team ELOs to {write_file}.")
    except IOError as e:
        print(f"[🔴] Error writing to {write_file}: {e}")

if __name__ == "__main__":
    # Example usage for standalone testing
    read_file = "json files/match_results.json"
    write_file = "json files/team_elos.json"
    start_calculating(read_file, write_file)
    sort_and_print(write_file)