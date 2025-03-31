# Import required libraries
import requests  # For making HTTP requests to the MLB API
from datetime import datetime  # For working with dates and times
from tabulate import tabulate  # For pretty-printing tables
from colorama import Fore, Back, Style, init  # For colored console output
import time  # For adding delays between API requests

# Initialize colorama to automatically reset colors after each print
init(autoreset=True)

def get_todays_games():
    """Fetch all completed MLB games for today from the API"""
    # Format today's date as YYYY-MM-DD for the API request
    today = datetime.now().strftime('%Y-%m-%d')
    # Construct the API URL for today's schedule
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}"
    
    try:
        # Make the API request with 10 second timeout
        response = requests.get(url, timeout=10)
        # Raise an exception for HTTP errors (4xx, 5xx)
        response.raise_for_status()
        # Parse the JSON response
        data = response.json()
        
        # Initialize empty list to store game info
        games = []
        # Check if the API returned any dates with games
        if data.get('dates'):
            # Loop through each date (usually just today)
            for date in data['dates']:
                # Loop through each game on this date
                for game in date['games']:
                    # Skip games that haven't started or were postponed
                    if game['status']['detailedState'] in ['Scheduled', 'Postponed']:
                        continue
                        
                    # Extract relevant game information into a dictionary
                    game_info = {
                        'game_pk': game['gamePk'],  # Unique game identifier
                        'away_team': game['teams']['away']['team']['name'],
                        'home_team': game['teams']['home']['team']['name'],
                        'status': game['status']['detailedState'],
                        'away_score': game['teams']['away'].get('score', 0),
                        'home_score': game['teams']['home'].get('score', 0),
                        'game_date': game['gameDate'],  # ISO format datetime
                        'venue': game['venue']['name'],
                        'game_type': game['gameType']  # Regular season, playoff, etc.
                    }
                    # Add this game's info to our list
                    games.append(game_info)
        return games
    
    except requests.exceptions.RequestException as e:
        # Print error in red if API request fails
        print(f"{Fore.RED}Error fetching games: {e}")
        return None

def get_game_data(game_pk):
    """Fetch detailed data for a specific game using multiple API endpoints"""
    # List of potential endpoints to try (in order of preference)
    endpoints = [
        f"https://statsapi.mlb.com/api/v1/game/{game_pk}/linescore",  # Basic game stats
        f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore",  # Detailed boxscore
        f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live/diffPatch"  # Live feed alternative
    ]
    
    # Try each endpoint until we get successful data
    for endpoint in endpoints:
        try:
            # Make the API request with 5 second timeout
            response = requests.get(endpoint, timeout=5)
            # If response is successful (status code 200)
            if response.status_code == 200:
                # Return the parsed JSON data
                return response.json()
            # Small delay to avoid hitting rate limits
            time.sleep(0.5)
        except requests.exceptions.RequestException:
            # If request fails, try the next endpoint
            continue
    
    # Return None if all endpoints fail
    return None

def get_team_stats(boxscore_data, team_type):
    """Extract team statistics from boxscore data with fallback defaults"""
    # Return default stats if no boxscore data is available
    if not boxscore_data or 'teams' not in boxscore_data or team_type not in boxscore_data['teams']:
        return {
            'hits': 0,
            'errors': 0,
            'home_runs': 0,
            'strikeouts': 0,
            'walks': 0,
            'avg': '.000'
        }
    
    # Get the specific team's data from boxscore
    team = boxscore_data['teams'][team_type]
    # Get batting stats with empty dict as fallback
    stats = team.get('teamStats', {}).get('batting', {})
    
    # Return stats with fallback values if data is missing
    return {
        'hits': stats.get('hits', team.get('hits', 0)),  # Try multiple locations for hits
        'errors': stats.get('errors', team.get('errors', 0)),
        'home_runs': stats.get('homeRuns', 0),
        'strikeouts': stats.get('strikeOuts', 0),
        'walks': stats.get('baseOnBalls', 0),
        'avg': stats.get('avg', '.000')  # Default to .000 if average not available
    }

def display_game_summary(game_info, game_data):
    """Display a detailed summary of the selected game"""
    # If no detailed game data is available, show basic info
    if not game_data:
        print(f"{Fore.YELLOW}Detailed stats not available for this game.")
        print(f"{Fore.CYAN}Basic Info: {game_info['away_team']} {game_info['away_score']} - {game_info['home_team']} {game_info['home_score']}")
        print(f"Status: {game_info['status']} | Venue: {game_info['venue']}")
        return
    
    # Extract basic game info from the dictionary
    away_team = game_info['away_team']
    home_team = game_info['home_team']
    away_score = game_info['away_score']
    home_score = game_info['home_score']
    # Parse and format the game time
    game_time = datetime.strptime(game_info['game_date'], "%Y-%m-%dT%H:%M:%SZ").strftime("%I:%M %p")
    venue = game_info['venue']
    
    # Determine winner and set colors for output
    if away_score > home_score:
        away_color = Fore.GREEN  # Winning team in green
        home_color = Fore.RED    # Losing team in red
        result = f"{away_team} win"
    elif home_score > away_score:
        away_color = Fore.RED    # Losing team in red
        home_color = Fore.GREEN  # Winning team in green
        result = f"{home_team} win"
    else:
        away_color = home_color = Fore.YELLOW  # Tie game in yellow
        result = "Tie"
    
    # Extract detailed stats from different possible data structures
    linescore = game_data if 'innings' in game_data else game_data.get('liveData', {}).get('linescore', {})
    boxscore = game_data if 'teams' in game_data else game_data.get('liveData', {}).get('boxscore', {})
    
    # Get statistics for both teams
    away_stats = get_team_stats(boxscore, 'away')
    home_stats = get_team_stats(boxscore, 'home')
    
    # Print game header with divider line
    print("\n" + "="*70)
    print(f"{away_team} vs {home_team}".center(70))  # Center the title
    print(f"{venue} | {game_time} | {result}".center(70))
    print("="*70)
    
    # Display inning-by-inning summary if available
    if 'innings' in linescore:
        innings = linescore['innings']
        inning_table = []
        
        # Process each inning's data
        for inning in innings:
            inning_num = inning['num']
            away_runs = inning['away'].get('runs', 0)  # Get runs with 0 as default
            home_runs = inning['home'].get('runs', 0)
            # Add inning info to table with appropriate colors
            inning_table.append([
                f"Inning {inning_num}",
                away_color + str(away_runs),
                home_color + str(home_runs)
            ])
        
        # Add totals row to the inning table
        inning_table.append([
            "TOTAL",
            away_color + str(away_score),
            home_color + str(home_score)
        ])
        
        # Print the inning table using tabulate
        print("\nInning-by-Inning Summary:")
        print(tabulate(
            inning_table,
            headers=["", away_team[:15], home_team[:15]],  # Truncate long team names
            tablefmt="grid"  # Use grid format for nice borders
        ))
    else:
        # Fallback if inning data isn't available
        print(f"\n{Fore.YELLOW}Inning-by-inning data not available")
        print(f"Final Score: {away_team} {away_score} - {home_team} {home_score}")
    
    # Prepare detailed stats table
    stats_table = [
        ["Hits", away_stats['hits'], home_stats['hits']],
        ["Errors", away_stats['errors'], home_stats['errors']],
        ["Home Runs", away_stats['home_runs'], home_stats['home_runs']],
        ["Strikeouts", away_stats['strikeouts'], home_stats['strikeouts']],
        ["Walks", away_stats['walks'], home_stats['walks']],
        ["Batting Avg", away_stats['avg'], home_stats['avg']]
    ]
    
    # Print the detailed stats table
    print("\nDetailed Stats:")
    print(tabulate(
        stats_table,
        headers=["Stat", away_team[:15], home_team[:15]],
        tablefmt="grid"
    ))

def main():
    """Main program execution"""
    # Try to import required packages
    try:
        from tabulate import tabulate
        from colorama import Fore, Back, Style, init
    except ImportError:
        # If packages are missing, install them automatically
        print("Installing required packages...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tabulate", "colorama"])
        from tabulate import tabulate
        from colorama import Fore, Back, Style, init
        init(autoreset=True)
    
    # Print program header in cyan
    print(Fore.CYAN + "\nMLB Game Inning Summarizer")
    print(Fore.CYAN + "="*30)
    print(Fore.CYAN + f"Date: {datetime.now().strftime('%A, %B %d, %Y')}\n")
    
    # Get today's games
    games = get_todays_games()
    
    # Handle case where no games are found
    if not games:
        print(Fore.YELLOW + "No completed games found for today.")
        return
    
    # Print list of today's games
    print(Fore.CYAN + "Today's MLB Games:")
    for i, game in enumerate(games, 1):  # Start numbering at 1
        # Use yellow for in-progress games, white for final
        score_color = Fore.YELLOW if game['status'] != 'Final' else Fore.WHITE
        print(f"{i}. {game['away_team']} @ {game['home_team']} - " +
              f"{score_color}{game['away_score']}-{game['home_score']} " +
              f"({game['status']})")
    
    # Main interaction loop
    while True:
        try:
            # Get user input
            choice = input("\nEnter game number to see details (q to quit): ")
            if choice.lower() == 'q':
                break  # Exit loop if user quits
            
            # Convert to integer and validate
            choice = int(choice)
            if 1 <= choice <= len(games):
                # Get selected game info
                selected_game = games[choice-1]
                print(f"\nLoading {selected_game['away_team']} @ {selected_game['home_team']}...")
                # Fetch detailed game data
                game_data = get_game_data(selected_game['game_pk'])
                # Display the summary
                display_game_summary(selected_game, game_data)
            else:
                # Handle invalid selection
                print(Fore.RED + "Invalid selection. Please try again.")
        except ValueError:
            # Handle non-numeric input
            print(Fore.RED + "Please enter a valid number or 'q' to quit.")

# Standard Python idiom to execute main() when script is run directly
if __name__ == "__main__":
    main()