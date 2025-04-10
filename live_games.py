import requests
import random
import time
from datetime import datetime

class MLBGameStat:
    def __init__(self):
        self.base_url = "https://statsapi.mlb.com/api/v1/"
        self.game_id = None
        self.home_team = None
        self.away_team = None
        self.last_play_id = 0
        self.batter_stats = {}
        self.pitcher_stats = {}
        self.commentary_flavors = {
            'strikeout': [
                "And he goes down swinging!",
                "Swings and misses, that's strike three!",
                "Loses the battle, strikeout!"
            ],
            'walk': [
                "And he takes ball four for a walk.",
                "Works the count and draws the walk.",
                "Free pass issued to the batter."
            ],
            'single': [
                "Lines it into left field for a single!",
                "Base hit up the middle!",
                "Drops it in shallow center for a single.",
                "Ground ball finds a hole! Runner on first."
            ],
            'double': [
                "Ripped into the gap! That's a stand-up double!",
                "Off the wall! He's in at second with a double.",
                "Lined down the line for a two-bagger!"
            ],
            'triple': [
                "Driven deep to right center! He's going for three!",
                "Gap shot! The outfielder can't cut it off - triple!",
                "Off the wall and it gets away! Triple for the batter!"
            ],
            'homerun': [
                "HIGH FLY BALL... DEEP LEFT FIELD... GONE! HOME RUN!",
                "CRUSHED! That ball is way outta here!",
                "Launches one to the upper deck! Homerun!",
                "No doubt about it! That's a moonshot!"
            ],
            'groundout': [
                "Ground ball to short, throw to first... out.",
                "Chopper to third, easy play for the out.",
                "Rolls over it, ground out to second base."
            ],
            'flyout': [
                "High fly ball to left, caught for the out.",
                "Can of corn to center field.",
                "Lazy pop fly to the infield, caught."
            ],
            'double_play': [
                "Ground ball... turn two! Double play!",
                "One-hopper to short, around the horn for two!",
                "Perfect double play ball to second base."
            ],
            'wild_pitch': [
                "Wild pitch! The runner advances!",
                "Gets away from the catcher!",
                "Spiked in the dirt, gets past the backstop."
            ],
            'passed_ball': [
                "Passed ball! Runner moves up!",
                "Catcher can't handle it!",
                "Tips off the glove, runner takes the base."
            ],
            'steal': [
                "Runner goes! SAFE at second base!",
                "Great jump! Stolen base!",
                "Slide... SAFE! Stolen base successful."
            ],
            'pitching_change': [
                "And here comes the manager, making a pitching change.",
                "Bullpen gate swings open, new arm coming in.",
                "They're going to the pen for a fresh arm."
            ]
        }
    
    def get_live_games(self):
        """Get list of live MLB games"""
        url = f"{self.base_url}schedule?sportId=1"
        response = requests.get(url)
        data = response.json()
        
        live_games = []
        today = datetime.now().strftime("%Y-%m-%d")
        
        if 'dates' in data and len(data['dates']) > 0:
            for game in data['dates'][0]['games']:
                if game['status']['abstractGameState'] == 'Live':
                    live_games.append({
                        'game_id': game['gamePk'],
                        'home_team': game['teams']['home']['team']['name'],
                        'away_team': game['teams']['away']['team']['name'],
                        'status': game['status']['detailedState']
                    })
        
        return live_games
    
    def select_game(self, games):
        """Select a game from the list of live games"""
        if not games:
            print("No live games currently available.")
            return None
        
        print("\nCurrent Live MLB Games:")
        for i, game in enumerate(games, 1):
            print(f"{i}. {game['away_team']} @ {game['home_team']} - {game['status']}")
        
        while True:
            choice = input("\nSelect a game (1-{}) or Q to quit: ".format(len(games)))
            if choice.upper() == 'Q':
                return None
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(games):
                    return games[idx]
            except ValueError:
                print("Invalid selection. Please try again.")
    
    def get_game_data(self, game_id):
        """Get current game data"""
        url = f"{self.base_url}game/{game_id}/feed/live"
        response = requests.get(url)
        return response.json()
    
    def get_play_description(self, play):
        """Get the official play description"""
        return play['result']['description']
    
    def generate_commentary(self, play):
        """Generate simulated commentary for a play"""
        event_type = play['result']['eventType']
        description = self.get_play_description(play)
        
        # Default commentary is the official description
        commentary = description
        
        # Add flavor text based on event type
        if event_type in self.commentary_flavors:
            flavor = random.choice(self.commentary_flavors[event_type])
            commentary = f"{flavor} {description}"
        
        # Add context about the game situation
        runners = play.get('runners', [])
        if runners:
            runner_text = []
            for runner in runners:
                if runner['movement']['end'] != runner['movement']['start']:
                    runner_text.append(f"Runner from {runner['movement']['start']} to {runner['movement']['end']}")
            if runner_text:
                commentary += " " + ", ".join(runner_text) + "."
        
        # Add count information if available
        if 'count' in play:
            count = play['count']
            balls = count['balls']
            strikes = count['strikes']
            outs = play.get('outs', 0)
            commentary += f" Count was {balls}-{strikes} with {outs} out(s)."
        
        return commentary
    
    def get_player_name(self, player_id):
        """Get player name from ID"""
        url = f"{self.base_url}people/{player_id}"
        response = requests.get(url)
        data = response.json()
        return data['people'][0]['fullName']
    
    def simulate_game(self, game_id, home_team, away_team):
        """Simulate play-by-play for a selected game"""
        self.game_id = game_id
        self.home_team = home_team
        self.away_team = away_team
        
        print(f"\nStarting play-by-play simulation for {away_team} @ {home_team}")
        print("Press Ctrl+C to stop the simulation at any time.\n")
        
        try:
            while True:
                game_data = self.get_game_data(game_id)
                current_plays = game_data['liveData']['plays']['allPlays']
                
                # Only process new plays we haven't seen yet
                if len(current_plays) > self.last_play_id:
                    for play in current_plays[self.last_play_id:]:
                        # Get batter and pitcher names
                        batter_id = play['matchup']['batter']['id']
                        pitcher_id = play['matchup']['pitcher']['id']
                        batter_name = self.get_player_name(batter_id)
                        pitcher_name = self.get_player_name(pitcher_id)
                        
                        # Generate commentary
                        commentary = self.generate_commentary(play)
                        
                        # Print the play
                        print(f"\n{play['about']['inning']} {play['about']['halfInning'].capitalize()}")
                        print(f"Batter: {batter_name} vs Pitcher: {pitcher_name}")
                        print(commentary)
                        
                        # Update stats
                        self.update_stats(play, batter_id, pitcher_id)
                        
                        # Small delay for readability
                        time.sleep(3)
                    
                    self.last_play_id = len(current_plays)
                
                # Check if game is over
                if game_data['gameData']['status']['abstractGameState'] == 'Final':
                    print("\nGame over! Final score:")
                    home_score = game_data['liveData']['linescore']['teams']['home']['runs']
                    away_score = game_data['liveData']['linescore']['teams']['away']['runs']
                    print(f"{self.away_team} {away_score} - {self.home_team} {home_score}")
                    break
                
                # Wait before checking for new plays
                time.sleep(10)
        
        except KeyboardInterrupt:
            print("\nSimulation stopped by user.")
    
    def update_stats(self, play, batter_id, pitcher_id):
        """Update batter and pitcher stats based on play"""
        event_type = play['result']['eventType']
        
        # Initialize stats if not present
        if batter_id not in self.batter_stats:
            self.batter_stats[batter_id] = {'name': self.get_player_name(batter_id), 'ab': 0, 'h': 0, 'hr': 0, 'rbi': 0}
        if pitcher_id not in self.pitcher_stats:
            self.pitcher_stats[pitcher_id] = {'name': self.get_player_name(pitcher_id), 'ip': 0, 'h': 0, 'er': 0, 'so': 0}
        
        # Update batter stats
        if event_type in ['single', 'double', 'triple', 'homerun']:
            self.batter_stats[batter_id]['h'] += 1
            if event_type == 'homerun':
                self.batter_stats[batter_id]['hr'] += 1
            # Increment AB for hits
            self.batter_stats[batter_id]['ab'] += 1
        
        # Update pitcher stats
        if event_type in ['single', 'double', 'triple', 'homerun']:
            self.pitcher_stats[pitcher_id]['h'] += 1
            # For simplicity, assume all runs are earned
            if 'rbi' in play['result']:
                self.pitcher_stats[pitcher_id]['er'] += play['result']['rbi']
        elif event_type == 'strikeout':
            self.pitcher_stats[pitcher_id]['so'] += 1
    
    def print_stats(self):
        """Print current batter and pitcher stats"""
        print("\nCurrent Batter Stats:")
        for batter in self.batter_stats.values():
            avg = round(batter['h'] / batter['ab'], 3) if batter['ab'] > 0 else 0.000
            print(f"{batter['name']}: {batter['h']}-{batter['ab']} (.{int(avg*1000):03d}), {batter['hr']} HR")
        
        print("\nCurrent Pitcher Stats:")
        for pitcher in self.pitcher_stats.values():
            era = round((pitcher['er'] * 9) / (pitcher['ip'] if pitcher['ip'] > 0 else 1), 2)
            print(f"{pitcher['name']}: {pitcher['ip']} IP, {pitcher['h']} H, {pitcher['er']} ER, {pitcher['so']} K, ERA: {era}")

def main():
    simulator = MLBGameStat()
    
    while True:
        live_games = simulator.get_live_games()
        selected_game = simulator.select_game(live_games)
        
        if not selected_game:
            print("Exiting")
            break
        
        simulator.simulate_game(
            selected_game['game_id'],
            selected_game['home_team'],
            selected_game['away_team']
        )
        
        # Print stats at the end of the game
        simulator.print_stats()
        
        # Ask if user wants to follow another game
        choice = input("\nWould you like to check another game? (Y/N): ")
        if choice.upper() != 'Y':
            print("Thanks for using")
            break
        
        # Reset for new game
        simulator.last_play_id = 0
        simulator.batter_stats = {}
        simulator.pitcher_stats = {}

if __name__ == "__main__":
    main()