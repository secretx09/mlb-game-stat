import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time

class MLBGamesTracker:
    def __init__(self):
        self.base_url = "https://www.mlb.com/scores"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def get_all_games(self):
        """Get all games for today"""
        try:
            response = requests.get(self.base_url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            games = []
            game_cards = soup.find_all('div', class_='game-card-wrapper')
            
            for card in game_cards:
                game = self._parse_game_card(card)
                if game:
                    games.append(game)
            
            return games
            
        except Exception as e:
            print(f"Error getting games: {e}")
            return []
    
    def _parse_game_card(self, card):
        """Parse individual game card"""
        try:
            # Basic game info
            game_id = card.find('a', class_='game-card-link')['href'].split('/')[-1]
            teams = card.find_all('span', class_='team-name--abbrev')
            away_team = teams[0].text if len(teams) > 0 else None
            home_team = teams[1].text if len(teams) > 1 else None
            
            # Scores
            scores = card.find_all('span', class_='score')
            away_score = scores[0].text if len(scores) > 0 else None
            home_score = scores[1].text if len(scores) > 1 else None
            
            # Game status
            status_div = card.find('div', class_='game-status')
            status = status_div.text.strip() if status_div else None
            
            # Detailed status (inning, outs, etc.)
            detail_status = card.find('div', class_='game-status-detail')
            detail_text = detail_status.text.strip() if detail_status else None
            
            # Get detailed game info if available
            game_url = f"https://www.mlb.com/gameday/{game_id}"
            game_details = self._get_game_details(game_url) if game_id else {}
            
            return {
                'game_id': game_id,
                'away_team': away_team,
                'home_team': home_team,
                'away_score': away_score,
                'home_score': home_score,
                'status': status,
                'detail_status': detail_text,
                **game_details
            }
            
        except Exception as e:
            print(f"Error parsing game card: {e}")
            return None
    
    def _get_game_details(self, game_url):
        """Get detailed game information from game page"""
        try:
            details = {}
            response = requests.get(game_url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Current at-bat information
            at_bat = soup.find('div', class_='at-bat')
            if at_bat:
                batter = at_bat.find('span', class_='batter-name')
                pitcher = at_bat.find('span', class_='pitcher-name')
                count = at_bat.find('div', class_='count')
                
                details['current_batter'] = batter.text.strip() if batter else None
                details['current_pitcher'] = pitcher.text.strip() if pitcher else None
                details['current_count'] = count.text.strip() if count else None
            
            # Game situation (outs, runners, etc.)
            situation = soup.find('div', class_='situation')
            if situation:
                outs = situation.find('div', class_='outs')
                runners = situation.find_all('div', class_='runner')
                
                details['outs'] = outs.text.strip() if outs else None
                details['runners'] = [runner.text.strip() for runner in runners] if runners else []
            
            # Line score (innings)
            line_score = soup.find('div', class_='linescore')
            if line_score:
                innings = line_score.find_all('div', class_='inning')
                details['innings'] = [inning.text.strip() for inning in innings]
            
            # Box score data
            box_score = soup.find('div', class_='boxscore')
            if box_score:
                team_stats = box_score.find_all('div', class_='team-stats')
                if len(team_stats) >= 2:
                    details['away_stats'] = self._parse_team_stats(team_stats[0])
                    details['home_stats'] = self._parse_team_stats(team_stats[1])
            
            return details
            
        except Exception as e:
            print(f"Error getting game details: {e}")
            return {}
    
    def _parse_team_stats(self, team_div):
        """Parse team statistics from box score"""
        stats = {}
        try:
            # Team name
            name = team_div.find('div', class_='team-name')
            stats['team'] = name.text.strip() if name else None
            
            # Hits and errors
            hits_errors = team_div.find('div', class_='hits-errors')
            if hits_errors:
                parts = hits_errors.text.strip().split(',')
                if len(parts) >= 1:
                    stats['hits'] = parts[0].replace('H', '').strip()
                if len(parts) >= 2:
                    stats['errors'] = parts[1].replace('E', '').strip()
            
            # Player stats
            batters = []
            batter_rows = team_div.find_all('tr', class_='batter')
            for row in batter_rows:
                cols = row.find_all('td')
                if len(cols) >= 8:  # Typical number of columns
                    batter = {
                        'name': cols[0].text.strip(),
                        'pos': cols[1].text.strip(),
                        'ab': cols[2].text.strip(),
                        'r': cols[3].text.strip(),
                        'h': cols[4].text.strip(),
                        'rbi': cols[5].text.strip(),
                        'bb': cols[6].text.strip(),
                        'so': cols[7].text.strip(),
                        'avg': cols[8].text.strip() if len(cols) > 8 else None
                    }
                    batters.append(batter)
            
            stats['batters'] = batters
            
            pitchers = []
            pitcher_rows = team_div.find_all('tr', class_='pitcher')
            for row in pitcher_rows:
                cols = row.find_all('td')
                if len(cols) >= 7:  # Typical number of columns
                    pitcher = {
                        'name': cols[0].text.strip(),
                        'ip': cols[1].text.strip(),
                        'h': cols[2].text.strip(),
                        'r': cols[3].text.strip(),
                        'er': cols[4].text.strip(),
                        'bb': cols[5].text.strip(),
                        'so': cols[6].text.strip(),
                        'era': cols[7].text.strip() if len(cols) > 7 else None
                    }
                    pitchers.append(pitcher)
            
            stats['pitchers'] = pitchers
            
            return stats
            
        except Exception as e:
            print(f"Error parsing team stats: {e}")
            return stats
    
    def display_games(self, games):
        """Display all games in a nice format"""
        print("\nMLB Games -", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print("="*50)
        
        for i, game in enumerate(games, 1):
            print(f"\nGame {i}: {game['away_team']} @ {game['home_team']}")
            print(f"Score: {game['away_team']} {game['away_score']} - {game['home_team']} {game['home_score']}")
            print(f"Status: {game['status']} - {game['detail_status']}")
            
            if 'outs' in game:
                print(f"\nCurrent Situation:")
                print(f"Outs: {game['outs']}")
                if game['runners']:
                    print(f"Runners: {', '.join(game['runners'])}")
                else:
                    print("Bases empty")
                
                if 'current_batter' in game:
                    print(f"\nAt Bat: {game['current_batter']}")
                    print(f"Pitcher: {game['current_pitcher']}")
                    print(f"Count: {game['current_count']}")
            
            if 'innings' in game:
                print("\nInning Scores:")
                print(" ".join(game['innings']))
            
            if 'away_stats' in game and 'home_stats' in game:
                print("\nTeam Stats:")
                print(f"{game['away_stats']['team']}: {game['away_stats']['hits']} H, {game['away_stats']['errors']} E")
                print(f"{game['home_stats']['team']}: {game['home_stats']['hits']} H, {game['home_stats']['errors']} E")
            
            print("-"*50)

def main():
    tracker = MLBGamesTracker()
    
    while True:
        try:
            games = tracker.get_all_games()
            if games:
                tracker.display_games(games)
            else:
                print("No games found or could not retrieve data.")
            
            # Refresh every 30 seconds
            time.sleep(30)
            print("\nRefreshing data...\n")
            
        except KeyboardInterrupt:
            print("\nExiting MLB Game Tracker...")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)  # Wait longer if error occurs

if __name__ == "__main__":
    main()