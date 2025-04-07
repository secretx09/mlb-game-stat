import requests
from datetime import datetime
from tabulate import tabulate
from colorama import Fore, Back, Style, init
import time

# Initialize colorama
init(autoreset=True)

def get_todays_games():
    today = datetime.now().strftime('%Y-%m-%d')
    return get_games_by_date(today)

def get_games_by_date(date):
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        games = []
        if data.get('dates'):
            for date in data['dates']:
                for game in date['games']:
                    # Skip games that haven't started or were postponed
                    if game['status']['detailedState'] in ['Scheduled', 'Postponed']:
                        continue
                        
                    game_info = {
                        'game_pk': game['gamePk'],
                        'away_team': game['teams']['away']['team']['name'],
                        'home_team': game['teams']['home']['team']['name'],
                        'status': game['status']['detailedState'],
                        'away_score': game['teams']['away'].get('score', 0),
                        'home_score': game['teams']['home'].get('score', 0),
                        'game_date': game['gameDate'],
                        'venue': game['venue']['name'],
                        'game_type': game['gameType']
                    }
                    games.append(game_info)
        return games
    
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}Error fetching games: {e}")
        return None

def get_game_data(game_pk):
    # Try multiple endpoints to get game data
    endpoints = [
        f"https://statsapi.mlb.com/api/v1/game/{game_pk}/linescore",
        f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore",
        f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live/diffPatch"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, timeout=5)
            if response.status_code == 200:
                return response.json()
            time.sleep(0.5)  # Brief delay between requests
        except requests.exceptions.RequestException:
            continue
    
    return None

def get_team_stats(boxscore_data, team_type):
    if not boxscore_data or 'teams' not in boxscore_data or team_type not in boxscore_data['teams']:
        return {
            'hits': 0,
            'errors': 0,
            'home_runs': 0,
            'strikeouts': 0,
            'walks': 0,
            'avg': '.000'
        }
    
    team = boxscore_data['teams'][team_type]
    stats = team.get('teamStats', {}).get('batting', {})
    
    return {
        'hits': stats.get('hits', team.get('hits', 0)),
        'errors': stats.get('errors', team.get('errors', 0)),
        'home_runs': stats.get('homeRuns', 0),
        'strikeouts': stats.get('strikeOuts', 0),
        'walks': stats.get('baseOnBalls', 0),
        'avg': stats.get('avg', '.000')
    }

def display_game_summary(game_info, game_data):
    if not game_data:
        print(f"{Fore.YELLOW}Detailed stats not available for this game.")
        print(f"{Fore.CYAN}Basic Info: {game_info['away_team']} {game_info['away_score']} - {game_info['home_team']} {game_info['home_score']}")
        print(f"Status: {game_info['status']} | Venue: {game_info['venue']}")
        return
    
    # Basic game info
    away_team = game_info['away_team']
    home_team = game_info['home_team']
    away_score = game_info['away_score']
    home_score = game_info['home_score']
    game_time = datetime.strptime(game_info['game_date'], "%Y-%m-%dT%H:%M:%SZ").strftime("%I:%M %p")
    venue = game_info['venue']
    
    # Determine winner and colors
    if away_score > home_score:
        away_color = Fore.GREEN
        home_color = Fore.RED
        result = f"{away_team} win"
    elif home_score > away_score:
        away_color = Fore.RED
        home_color = Fore.GREEN
        result = f"{home_team} win"
    else:
        away_color = home_color = Fore.YELLOW
        result = "Tie"
    
    # Get detailed stats from different possible endpoints
    linescore = game_data if 'innings' in game_data else game_data.get('liveData', {}).get('linescore', {})
    boxscore = game_data if 'teams' in game_data else game_data.get('liveData', {}).get('boxscore', {})
    
    away_stats = get_team_stats(boxscore, 'away')
    home_stats = get_team_stats(boxscore, 'home')
    
    # Display header
    print("\n" + "="*70)
    print(f"{away_team} vs {home_team}".center(70))
    print(f"{venue} | {game_time} | {result}".center(70))
    print("="*70)
    
    # Inning-by-inning summary (if available)
    if 'innings' in linescore:
        innings = linescore['innings']
        inning_table = []
        
        for inning in innings:
            inning_num = inning['num']
            away_runs = inning['away'].get('runs', 0)
            home_runs = inning['home'].get('runs', 0)
            inning_table.append([
                f"Inning {inning_num}",
                away_color + str(away_runs),
                home_color + str(home_runs)
            ])
        
        # Add totals with color coding
        inning_table.append([
            "TOTAL",
            away_color + str(away_score),
            home_color + str(home_score)
        ])
        
        print("\nInning-by-Inning Summary:")
        print(tabulate(
            inning_table,
            headers=["", away_team[:15], home_team[:15]],
            tablefmt="grid"
        ))
    else:
        print(f"\n{Fore.YELLOW}Inning-by-inning data not available")
        print(f"Final Score: {away_team} {away_score} - {home_team} {home_score}")
    
    # Detailed stats table
    stats_table = [
        ["Hits", away_stats['hits'], home_stats['hits']],
        ["Errors", away_stats['errors'], home_stats['errors']],
        ["Home Runs", away_stats['home_runs'], home_stats['home_runs']],
        ["Strikeouts", away_stats['strikeouts'], home_stats['strikeouts']],
        ["Walks", away_stats['walks'], home_stats['walks']],
        ["Batting Avg", away_stats['avg'], home_stats['avg']]
    ]
    
    print("\nDetailed Stats:")
    print(tabulate(
        stats_table,
        headers=["Stat", away_team[:15], home_team[:15]],
        tablefmt="grid"
    ))

def main():
    # Install required packages if missing
    try:
        from tabulate import tabulate
        from colorama import Fore, Back, Style, init
    except ImportError:
        print("Installing required packages...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tabulate", "colorama"])
        from tabulate import tabulate
        from colorama import Fore, Back, Style, init
        init(autoreset=True)
    
    print(Fore.CYAN + "\nMLB Game Inning Summarizer")
    print(Fore.CYAN + "="*30)
    print(Fore.CYAN + f"Date: {datetime.now().strftime('%A, %B %d, %Y')}\n")
    
    choice = input("Would you like to see today's games (t) or a previous day's games (p)? ")
    
    if choice.lower() == 't':
        today = datetime.now().strftime('%Y-%m-%d')
        games = get_games_by_date(today)
    elif choice.lower() == 'p':
        date_input = input("Enter the date (YYYY-MM-DD) of the games you want to see: ")
        try:
            datetime.strptime(date_input, '%Y-%m-%d')  # Validate date format
            games = get_games_by_date(date_input)
        except ValueError:
            print(Fore.RED + "Invalid date format. Please use YYYY-MM-DD.")
            return
    else:
        print(Fore.RED + "Invalid choice. Please select 't' or 'p'.")
        return
    
    if not games:
        print(Fore.YELLOW + "No completed games found for the selected date.")
        return
    
    print(Fore.CYAN + f"Games on {date_input if choice.lower() == 'p' else 'today'}:")
    for i, game in enumerate(games, 1):
        score_color = Fore.YELLOW if game['status'] != 'Final' else Fore.WHITE
        print(f"{i}. {game['away_team']} @ {game['home_team']} - " +
              f"{score_color}{game['away_score']}-{game['home_score']} " +
              f"({game['status']})")
    
    while True:
        try:
            choice = input("\nEnter game number to see details (q to quit): ")
            if choice.lower() == 'q':
                break
            
            choice = int(choice)
            if 1 <= choice <= len(games):
                selected_game = games[choice-1]
                print(f"\nLoading {selected_game['away_team']} @ {selected_game['home_team']}...")
                game_data = get_game_data(selected_game['game_pk'])
                display_game_summary(selected_game, game_data)
            else:
                print(Fore.RED + "Invalid selection. Please try again.")
        except ValueError:
            print(Fore.RED + "Please enter a valid number or 'q' to quit.")

if __name__ == "__main__":
    main()