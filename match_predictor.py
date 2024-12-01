import os
from openai import OpenAI
from dotenv import load_dotenv
import utils
from datetime import datetime
from get_teams import fetch_upcoming_matches
from teams import get_teams
from difflib import get_close_matches

# Dictionary mapping leagues to their API IDs (Free Tier Only)
LEAGUE_IDS = {
    # Major European Leagues
    "Premier League": "2021",
    "La Liga": "2014",
    "Bundesliga": "2002",
    "Serie A": "2019",
    "Ligue 1": "2015",
    "Eredivisie": "2003",
    "Championship": "2016",
    "Primeira Liga": "2017",
    
    # Major Competitions
    "Champions League": "2001",
    "World Cup": "2000",
    "European Championship": "2018",
    
    # Other Leagues
    "Brasileirão Serie A": "2013"
}

def find_closest_league(input_name, leagues):
    """Find the closest matching league name using fuzzy matching"""
    # Convert input and league names to lowercase for comparison
    input_lower = input_name.lower().strip()
    
    # First try exact match (case-insensitive)
    for league in leagues:
        if league.lower() == input_lower:
            return league
            
    # Then try 'contains' match
    for league in leagues:
        if input_lower in league.lower():
            return league
    
    # Try to find close matches
    matches = get_close_matches(input_name, leagues, n=3, cutoff=0.6)
    
    if matches:
        if len(matches) == 1:
            return matches[0]
        else:
            print("\nDid you mean one of these?")
            for i, match in enumerate(matches, 1):
                print(f"{i}. {match}")
            
            while True:
                choice = input("\nEnter the number of your choice (or 0 to try again): ").strip()
                if choice.isdigit():
                    choice = int(choice)
                    if 0 <= choice <= len(matches):
                        break
                print("Please enter a valid number.")
            
            if choice == 0:
                return None
            return matches[choice - 1]
    
    return None

class MatchPredictor:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.football_api_key = os.getenv('FOOTBALL_DATA_API_KEY')
        self.current_league = None
        self.fixtures = []
        self.current_batch_index = 0
        self.teams_data = {}  # Will store team IDs for current league

    def fetch_league_fixtures(self, league_name):
        """Fetch all fixtures for a given league"""
        if league_name not in LEAGUE_IDS:
            return False
        
        league_id = LEAGUE_IDS[league_name]
        print(f"\nFetching teams for {league_name} (ID: {league_id})...")
        
        # First, fetch teams for this league
        teams = get_teams(league_id, self.football_api_key)
        if not teams:
            print("Failed to fetch teams data!")
            return False
            
        # Store teams data in dictionary for quick lookup
        self.teams_data = {team['name']: str(team['id']) for team in teams}
        print(f"Found {len(self.teams_data)} teams in {league_name}")
        
        print(f"\nFetching fixtures...")
        self.fixtures = fetch_upcoming_matches(league_id, self.football_api_key)
        self.current_league = league_name
        self.current_batch_index = 0
        return bool(self.fixtures)

    def get_team_id(self, team_name):
        """Get team ID from stored teams data"""
        # Try exact match first
        team_id = self.teams_data.get(team_name)
        if team_id:
            return team_id
            
        # Try case-insensitive match
        team_name_lower = team_name.lower()
        for name, id in self.teams_data.items():
            if team_name_lower in name.lower():
                return id
        
        return None

    def format_match_data(self, comparison_data):
        """Format the match data into a readable string for ChatGPT"""
        output = []
        
        # Format team data
        for team_key in ['team1', 'team2']:
            team_data = comparison_data[team_key]
            output.append(f"\n{team_data['name']} Recent Form:")
            summary = team_data['summary']
            output.append(f"Last {summary['matches_played']} matches: {summary['wins']}W-{summary['draws']}D-{summary['losses']}L")
            output.append(f"Win Rate: {summary['win_rate']}%")
            
            output.append("\nRecent matches:")
            for match in team_data['match_history'][:5]:  # Last 5 matches
                output.append(f"{match['date']}: {match['home_team']} {match['score']} {match['away_team']}")

        # Format head-to-head data
        h2h = comparison_data.get('head_to_head')
        if h2h:
            output.append("\nHead-to-Head History:")
            stats = h2h['stats']
            output.append(f"Total Matches: {stats['total_matches']}")
            output.append(f"Goals Scored: {stats['total_goals']}")
            
            output.append("\nLast 5 head-to-head matches:")
            for match in h2h['matches'][:5]:
                output.append(f"{match['date']}: {match['home_team']} {match['score']} {match['away_team']}")

        return "\n".join(output)

    def compare_teams(self, team1_name, team2_name):
        """Compare two teams' recent performances and head-to-head record"""
        team1_id = self.get_team_id(team1_name)
        team2_id = self.get_team_id(team2_name)
        
        if not team1_id or not team2_id:
            return "One or both teams not found."
            
        # Get individual team analyses
        team1_matches = utils.get_team_matches(team1_id)
        team2_matches = utils.get_team_matches(team2_id)
        
        if not team1_matches:
            return f"No matches found for {team1_name}"
        if not team2_matches:
            return f"No matches found for {team2_name}"
        
        # Calculate basic stats for team1
        total_matches1 = len(team1_matches)
        wins1 = sum(1 for match in team1_matches if match['result'] == 'W')
        losses1 = sum(1 for match in team1_matches if match['result'] == 'L')
        draws1 = sum(1 for match in team1_matches if match['result'] == 'D')
        
        # Calculate basic stats for team2
        total_matches2 = len(team2_matches)
        wins2 = sum(1 for match in team2_matches if match['result'] == 'W')
        losses2 = sum(1 for match in team2_matches if match['result'] == 'L')
        draws2 = sum(1 for match in team2_matches if match['result'] == 'D')
        
        team1_analysis = {
            'name': team1_name,
            'match_history': team1_matches,
            'summary': {
                'matches_played': total_matches1,
                'wins': wins1,
                'draws': draws1,
                'losses': losses1,
                'win_rate': round((wins1 / total_matches1 * 100), 2) if total_matches1 > 0 else 0
            }
        }
        
        team2_analysis = {
            'name': team2_name,
            'match_history': team2_matches,
            'summary': {
                'matches_played': total_matches2,
                'wins': wins2,
                'draws': draws2,
                'losses': losses2,
                'win_rate': round((wins2 / total_matches2 * 100), 2) if total_matches2 > 0 else 0
            }
        }
        
        # Get head-to-head analysis
        h2h_analysis = utils.get_head_to_head(team1_id, team2_id)
        
        return {
            'team1': team1_analysis,
            'team2': team2_analysis,
            'head_to_head': h2h_analysis
        }

    def get_predictions(self, team1_name, team2_name):
        """Get match predictions using ChatGPT"""
        # Get match data
        comparison = self.compare_teams(team1_name, team2_name)
        if isinstance(comparison, str):
            return f"Error: {comparison}"

        # Format data for ChatGPT
        match_data = self.format_match_data(comparison)

        # Prepare prompt
        prompt = f"""Based on the following match data and head-to-head history for {team1_name} vs {team2_name}:

{match_data}

Using only the statistical and factual data provided, provide exactly 3 highly probable predictions for this match.

Requirements:
1. Each prediction must be directly supported by the data shown
2. Format as exactly 3 bullet points
3. Keep each prediction concise (max 15 words)
4. Focus on concrete outcomes (goals, win/loss, scoring patterns)
5. No explanations or analysis - just the predictions

Example format:
- Team A to win based on superior head-to-head record
- Over 2.5 goals to be scored in the match
- Both teams to score at least one goal"""

        try:
            # Get ChatGPT's response
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a football prediction expert. Provide exactly 3 bullet-point predictions. No explanations or analysis."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error getting predictions: {str(e)}"

    def process_next_batch(self, batch_size=3):
        """Process the next batch of fixtures"""
        if not self.fixtures or self.current_batch_index >= len(self.fixtures):
            return False

        end_index = min(self.current_batch_index + batch_size, len(self.fixtures))
        current_batch = self.fixtures[self.current_batch_index:end_index]
        results = []

        for match in current_batch:
            home_team = match['homeTeam']['name']
            away_team = match['awayTeam']['name']
            match_date = datetime.strptime(match['utcDate'], '%Y-%m-%dT%H:%M:%SZ')
            formatted_date = match_date.strftime('%B %d, %Y at %H:%M UTC')
            
            print(f"\nAnalyzing: {home_team} vs {away_team} ({formatted_date})")
            
            # Get team IDs for historical data
            home_team_id = self.get_team_id(home_team)
            away_team_id = self.get_team_id(away_team)
            
            if not home_team_id or not away_team_id:
                print(f"Warning: Could not find IDs for one or both teams: {home_team} ({home_team_id}), {away_team} ({away_team_id})")
                continue
                
            predictions = self.get_predictions(home_team, away_team)
            results.append({
                'match': f"{home_team} vs {away_team}",
                'date': formatted_date,
                'predictions': predictions
            })

        self.current_batch_index = end_index
        return results

def main():
    predictor = MatchPredictor()
    
    # Show available leagues
    print("Available leagues:")
    for league in sorted(LEAGUE_IDS.keys()):
        print(f"- {league}")
    
    # Get league selection from user
    while True:
        try:
            league_name = input("\nEnter league name: ").strip()
            
            # Try to find closest match if exact match not found
            if league_name.lower() not in [l.lower() for l in LEAGUE_IDS.keys()]:
                closest_match = find_closest_league(league_name, LEAGUE_IDS.keys())
                if closest_match:
                    confirm = input(f"\nDid you mean '{closest_match}'? (yes/no): ").strip().lower()
                    if confirm == 'yes':
                        league_name = closest_match
                    else:
                        continue
                else:
                    print("Invalid league name. Please choose from the available leagues.")
                    continue
            else:
                # Find the correct case version
                league_name = next(l for l in LEAGUE_IDS.keys() if l.lower() == league_name.lower())
            
            break
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            return
    
    # Fetch fixtures and team data
    if not predictor.fetch_league_fixtures(league_name):
        print("Failed to fetch fixtures or no upcoming matches found.")
        return

    # Process fixtures in batches
    while True:
        results = predictor.process_next_batch(batch_size=3)
        if not results:
            print("\nNo more fixtures to analyze.")
            break

        # Display predictions for current batch
        for result in results:
            print(f"\nMatch: {result['match']} ({result['date']})")
            print("Predictions:")
            print(result['predictions'])
            print("-" * 50)

        # Ask user if they want to continue
        if predictor.current_batch_index < len(predictor.fixtures):
            continue_analysis = input("\nWould you like to see predictions for the next 3 matches? (yes/no): ").strip().lower()
            if continue_analysis != 'yes':
                break

if __name__ == "__main__":
    main() 