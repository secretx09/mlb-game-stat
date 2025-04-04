import requests
import random
import time
from datetime import datetime

class MLBGameSimulator:
    def __init__(self):
        self.base_url = "https://statsapi.mlb.com/api/v1/"
        self.game_id = None
        self.home_team = None
        self.away_team = None
        self.last_play_id = 0
        self.current_runners = {'1B': None, '2B': None, '3B': None}
        self.batter_stats = {}
        self.pitcher_stats = {}
        
        # Enhanced commentary with more situational awareness
        self.commentary_flavors = {
            'strikeout': [
                "And he goes down swinging!",
                "Strike three called! That's a nasty breaking ball.",
                "Fans him with high heat!",
                "Swings through the fastball for strike three!",
                "Paints the corner with a perfect pitch!"
            ],
            # [Previous event types remain the same...]
        }
    
    def draw_diamond(self):
        """Draw an ASCII baseball diamond showing runner positions"""
        base_names = {
            '1B': "1st",
            '2B': "2nd",
            '3B': "3rd"
        }
        
        diamond = f"""
        {' ' * 15}{'◼' if self.current_runners['3B'] else '◻'} 3B
        {' ' * 10}{'◼' if self.current_runners['2B'] else '◻'} 2B{' ' * 10}
        {' ' * 5}{'◼' if self.current_runners['1B'] else '◻'} 1B{' ' * 20}
        {' ' * 10}⯆{' ' * 10}
        """
        
        # Add runner names if present
        runner_info = []
        for base, runner in self.current_runners.items():
            if runner:
                runner_info.append(f"{base_names[base]}: {self.get_player_name(runner)}")
        
        return diamond + ("\nRunners: " + ", ".join(runner_info) if runner_info else "")

    def update_runners(self, play):
        """Update runner positions based on the play"""
        # Clear current runners
        self.current_runners = {'1B': None, '2B': None, '3B': None}
        
        # Update based on play data
        if 'runners' in play:
            for runner in play['runners']:
                end_base = runner['movement']['end']
                if end_base in ['1B', '2B', '3B']:
                    self.current_runners[end_base] = runner['details']['runner']['id']
        
        # Handle batter becoming runner (e.g., on a hit)
        if play['result']['eventType'] in ['single', 'double', 'triple', 'homerun', 'walk']:
            batter_id = play['matchup']['batter']['id']
            if play['result']['eventType'] == 'single':
                self.current_runners['1B'] = batter_id
            elif play['result']['eventType'] == 'double':
                self.current_runners['2B'] = batter_id
            elif play['result']['eventType'] == 'triple':
                self.current_runners['3B'] = batter_id
            elif play['result']['eventType'] == 'homerun':
                pass  # All runners score, diamond clears
            elif play['result']['eventType'] == 'walk' and not any(self.current_runners.values()):
                self.current_runners['1B'] = batter_id

    def simulate_game(self, game_id, home_team, away_team):
        """Simulate play-by-play for a selected game with diamond visualization"""
        self.game_id = game_id
        self.home_team = home_team
        self.away_team = away_team
        
        print(f"\nStarting play-by-play simulation for {away_team} @ {home_team}")
        print("Press Ctrl+C to stop the simulation at any time.\n")
        
        try:
            while True:
                game_data = self.get_game_data(game_id)
                current_plays = game_data['liveData']['plays']['allPlays']
                
                if len(current_plays) > self.last_play_id:
                    for play in current_plays[self.last_play_id:]:
                        # Clear screen for better visibility (works in most terminals)
                        print("\033c", end="")
                        
                        # Update runner positions
                        self.update_runners(play)
                        
                        # Get player names
                        batter_id = play['matchup']['batter']['id']
                        pitcher_id = play['matchup']['pitcher']['id']
                        batter_name = self.get_player_name(batter_id)
                        pitcher_name = self.get_player_name(pitcher_id)
                        
                        # Generate and display play info
                        print(f"{'='*50}")
                        print(f"Inning: {play['about']['inning']} {play['about']['halfInning'].capitalize()}")
                        print(f"Batter: {batter_name} vs Pitcher: {pitcher_name}")
                        print(f"Score: {away_team} {game_data['liveData']['linescore']['teams']['away']['runs']} - "
                              f"{home_team} {game_data['liveData']['linescore']['teams']['home']['runs']}")
                        print(f"Outs: {play.get('outs', 0)}")
                        
                        # Display the baseball diamond
                        print(self.draw_diamond())
                        
                        # Show play commentary
                        commentary = self.generate_commentary(play)
                        print(f"\n{commentary}")
                        
                        # Update stats
                        self.update_stats(play, batter_id, pitcher_id)
                        
                        # Small delay for readability
                        time.sleep(5)
                    
                    self.last_play_id = len(current_plays)
                
                # Check if game is over
                if game_data['gameData']['status']['abstractGameState'] == 'Final':
                    print("\nGame over! Final score:")
                    home_score = game_data['liveData']['linescore']['teams']['home']['runs']
                    away_score = game_data['liveData']['linescore']['teams']['away']['runs']
                    print(f"{self.away_team} {away_score} - {self.home_team} {home_score}")
                    break
                
                time.sleep(10)  # Wait before checking for new plays
        
        except KeyboardInterrupt:
            print("\nSimulation stopped by user.")

# [Rest of the class methods remain the same...]