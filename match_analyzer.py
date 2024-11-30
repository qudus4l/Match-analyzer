import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import pandas as pd
from tabulate import tabulate

# Load environment variables
load_dotenv()

class MatchAnalyzer:
    def __init__(self):
        self.api_key = os.getenv('FOOTBALL_DATA_API_KEY')
        self.base_url = 'http://api.football-data.org/v4'
        self.headers = {'X-Auth-Token': self.api_key}
        
        # Initialize with comprehensive Premier League team mappings
        self.team_ids = {
            'arsenal': 57, 'arsenal fc': 57,
            'aston villa': 58, 'aston villa fc': 58,
            'chelsea': 61, 'chelsea fc': 61,
            'everton': 62, 'everton fc': 62,
            'fulham': 63, 'fulham fc': 63,
            'liverpool': 64, 'liverpool fc': 64,
            'manchester city': 65, 'man city': 65, 'city': 65,
            'manchester united': 66, 'man united': 66, 'man utd': 66,
            'newcastle': 67, 'newcastle united': 67,
            'tottenham': 73, 'spurs': 73, 'tottenham hotspur': 73,
            'wolves': 76, 'wolverhampton': 76, 'wolverhampton wanderers': 76,
            'leicester': 338, 'leicester city': 338,
            'southampton': 340, 'saints': 340,
            'ipswich': 349, 'ipswich town': 349,
            'nottingham': 351, 'forest': 351, 'nottingham forest': 351,
            'crystal palace': 354, 'palace': 354,
            'brighton': 397, 'brighton hove': 397, 'brighton & hove': 397,
            'brentford': 402,
            'west ham': 563, 'west ham united': 563,
            'bournemouth': 1044, 'afc bournemouth': 1044
        }

    def populate_team_ids(self):
        """Fetch and store Premier League team IDs from the API"""
        # Premier League competition ID is 2021
        url = f"{self.base_url}/competitions/2021/teams"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            teams = response.json()['teams']
            for team in teams:
                # Store both full name and short name as keys
                self.team_ids[team['name'].lower()] = team['id']
                if team['shortName']:
                    self.team_ids[team['shortName'].lower()] = team['id']
                    
            print(f"Loaded {len(teams)} Premier League team mappings")
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching team IDs: {str(e)}")
            # Fallback to basic mappings if API fails
            self.team_ids = {
                'manchester united': 66,
                'chelsea': 61,
                'arsenal': 57,
                'manchester city': 65,
                'liverpool': 64,
                'tottenham': 73
            }

    def get_team_id(self, team_name):
        """Get team ID with fuzzy matching fallback"""
        team_name_lower = team_name.lower()
        
        # Direct match
        if team_name_lower in self.team_ids:
            return self.team_ids[team_name_lower]
            
        # Partial match
        for known_name, team_id in self.team_ids.items():
            if team_name_lower in known_name or known_name in team_name_lower:
                return team_id
                
        # Fallback to API search if still no match
        url = f"{self.base_url}/teams"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            teams = response.json()['teams']
            for team in teams:
                if team_name.lower() in team['name'].lower():
                    return team['id']
        return None

    def compare_teams(self, team1_name, team2_name):
        """Compare two teams' recent performances and head-to-head record"""
        team1_id = self.get_team_id(team1_name)
        team2_id = self.get_team_id(team2_name)
        
        if not team1_id or not team2_id:
            return "One or both teams not found."
            
        # Get individual team analyses
        team1_analysis = self.analyze_team(team1_id, team1_name)
        team2_analysis = self.analyze_team(team2_id, team2_name)
        
        # Get head-to-head analysis
        h2h_analysis = self.get_head_to_head(team1_id, team2_id)
        
        return {
            'team1': team1_analysis,
            'team2': team2_analysis,
            'head_to_head': h2h_analysis
        }

    def analyze_team(self, team_id, team_name):
        """Show detailed match history and performance summary"""
        matches = self.get_team_matches(team_id)
        if not matches:
            return f"No matches found for {team_name}"
        
        # Calculate basic stats
        total_matches = len(matches)
        wins = sum(1 for match in matches if match['result'] == 'W')
        losses = sum(1 for match in matches if match['result'] == 'L')
        draws = sum(1 for match in matches if match['result'] == 'D')
        
        return {
            'name': team_name,
            'match_history': matches,
            'summary': {
                'matches_played': total_matches,
                'wins': wins,
                'draws': draws,
                'losses': losses,
                'win_rate': round((wins / total_matches * 100), 2) if total_matches > 0 else 0
            }
        }

    def get_team_matches(self, team_id, days_back=90):
        """Get detailed match history for a team"""
        date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        date_to = datetime.now().strftime('%Y-%m-%d')
        
        url = f"{self.base_url}/teams/{team_id}/matches"
        params = {
            'dateFrom': date_from,
            'dateTo': date_to,
            'status': 'FINISHED'
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            matches = response.json()['matches']
            match_history = []
            
            for match in matches:
                # Get match details
                date = datetime.strptime(match['utcDate'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
                home_team = match['homeTeam']['name']
                away_team = match['awayTeam']['name']
                score = match['score']['fullTime']
                competition = match['competition']['name']
                
                # Skip if no score (match not played)
                if not score['home'] and not score['away']:
                    continue
                    
                match_info = {
                    'date': date,
                    'competition': competition,
                    'home_team': home_team,
                    'away_team': away_team,
                    'score': f"{score['home']} - {score['away']}",
                    'result': self.get_result(match, team_id)
                }
                match_history.append(match_info)
                
            return match_history
        return []

    def get_result(self, match, team_id):
        """Determine if the team won, lost, or drew the match"""
        score = match['score']['fullTime']
        is_home = match['homeTeam']['id'] == team_id
        
        team_score = score['home'] if is_home else score['away']
        opponent_score = score['away'] if is_home else score['home']
        
        if team_score > opponent_score:
            return 'W'
        elif team_score < opponent_score:
            return 'L'
        else:
            return 'D'

    def get_head_to_head(self, team1_id, team2_id):
        """Get head to head matches between two teams"""
        # Get matches for team1
        url = f"{self.base_url}/teams/{team1_id}/matches"
        params = {
            'status': 'FINISHED',
            'limit': 200  # Increase limit to find matches
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()  # Raise exception for bad status codes
            
            matches = response.json()['matches']
            match_id = None
            
            # Find a match between these two teams
            for match in matches:
                if (match['homeTeam'].get('id') == team2_id or 
                    match['awayTeam'].get('id') == team2_id):
                    match_id = match['id']
                    break
            
            if not match_id:
                print(f"No matches found between teams {team1_id} and {team2_id}")
                return None
            
            # Get head to head data using the match ID
            url = f"{self.base_url}/matches/{match_id}/head2head"
            params = {'limit': 60}  # Get up to 50 previous matches
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            h2h_data = response.json()
            
            # Process the head to head data
            matches = []
            for match in h2h_data['matches']:
                match_info = {
                    'date': datetime.strptime(match['utcDate'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d'),
                    'competition': match['competition']['name'],
                    'home_team': match['homeTeam']['name'],
                    'away_team': match['awayTeam']['name'],
                    'score': f"{match['score']['fullTime']['home']} - {match['score']['fullTime']['away']}",
                    'venue': match.get('venue', 'Unknown')
                }
                matches.append(match_info)
            
            # Get aggregate stats
            agg = h2h_data['aggregates']
            stats = {
                'total_matches': agg['numberOfMatches'],
                'total_goals': agg['totalGoals'],
                'team1_wins': agg['homeTeam']['wins'] if agg['homeTeam']['id'] == team1_id else agg['awayTeam']['wins'],
                'team2_wins': agg['homeTeam']['wins'] if agg['homeTeam']['id'] == team2_id else agg['awayTeam']['wins'],
                'draws': agg['homeTeam']['draws']  # draws are same for both teams
            }
            
            return {
                'matches': matches,
                'stats': stats
            }
            
        except requests.exceptions.RequestException as e:
            print(f"API Error: {str(e)}")
            return None
        except Exception as e:
            print(f"Error processing head-to-head data: {str(e)}")
            return None

def main():
    analyzer = MatchAnalyzer()
    
    # Get team names from user
    team1_name = input("Enter first team name: ")
    team2_name = input("Enter second team name: ")
    
    # Get comparison
    comparison = analyzer.compare_teams(team1_name, team2_name)
    
    if isinstance(comparison, str):
        print(comparison)
        return
    
    # Display results for each team
    for team_key in ['team1', 'team2']:
        team_data = comparison[team_key]
        print(f"\nMatch History for {team_data['name']}")
        print("=" * 50)
        
        # Display summary
        summary = team_data['summary']
        print(f"Last {summary['matches_played']} matches:")
        print(f"Record: {summary['wins']}W-{summary['draws']}D-{summary['losses']}L")
        print(f"Win Rate: {summary['win_rate']}%")
        
        # Display match history in table format
        print("\nDetailed Match History:")
        matches_df = pd.DataFrame(team_data['match_history'])
        print(tabulate(matches_df, headers='keys', tablefmt='grid', showindex=False))
        print("\n")
    
    # Display head-to-head results
    h2h = comparison.get('head_to_head')
    if h2h:
        print("\nHead-to-Head Analysis")
        print("=" * 50)
        stats = h2h['stats']
        
        print(f"Total Matches: {stats['total_matches']}")
        print(f"Total Goals: {stats['total_goals']}")
        print(f"{team1_name} wins: {stats['team1_wins']}")
        print(f"{team2_name} wins: {stats['team2_wins']}")
        print(f"Draws: {stats['draws']}")
        
        print("\nRecent Head-to-Head Matches:")
        h2h_df = pd.DataFrame(h2h['matches'])
        print(tabulate(h2h_df, headers='keys', tablefmt='grid', showindex=False))
    else:
        print("\nNo head-to-head data available for these teams")

if __name__ == "__main__":
    main()