import os
from openai import OpenAI
from dotenv import load_dotenv
import utils
from datetime import datetime
from get_teams import fetch_upcoming_matches

class MatchPredictor:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.football_api_key = os.getenv('FOOTBALL_DATA_API_KEY')

    def get_upcoming_matches(self, team1_name, team2_name):
        """Get upcoming matches involving either team"""
        matches = fetch_upcoming_matches("2021", self.football_api_key)
        relevant_matches = []
        
        for match in matches:
            home_team = match['homeTeam']['name']
            away_team = match['awayTeam']['name']
            if ((team1_name.lower() in home_team.lower() and team2_name.lower() in away_team.lower()) or
                (team2_name.lower() in home_team.lower() and team1_name.lower() in away_team.lower())):
                # Convert UTC time to more readable format
                match_date = datetime.strptime(match['utcDate'], '%Y-%m-%dT%H:%M:%SZ')
                formatted_date = match_date.strftime('%B %d, %Y at %H:%M UTC')
                relevant_matches.append(f"{home_team} vs {away_team} on {formatted_date}")
        
        return relevant_matches

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
        team1_id = utils.get_team_id(team1_name)
        team2_id = utils.get_team_id(team2_name)
        
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

        # Get upcoming matches
        upcoming_matches = self.get_upcoming_matches(team1_name, team2_name)
        
        # Format data for ChatGPT
        match_data = self.format_match_data(comparison)

        # Prepare prompt
        prompt = f"""Here is the recent match data and head-to-head history for {team1_name} vs {team2_name}:

{match_data}

Upcoming matches involving these teams:
{chr(10).join(upcoming_matches) if upcoming_matches else "No upcoming matches found"}

Given only the statistical and factual data provided, generate predictions for each upcoming match listed above. For each match:
1. Analyze the specific matchup based on recent form and head-to-head history
2. Provide 3-5 highly probable (>90% likelihood) predictions
3. Clearly indicate the data source and confidence level for each prediction
4. Avoid speculative claims - use only the data provided

Important:
- Each prediction must be directly supported by the data shown
- If insufficient data exists for high-confidence predictions, state that explicitly
"""

        try:
            # Get ChatGPT's response
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a football analysis expert focused on data-driven predictions."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error getting predictions: {str(e)}"

def main():
    predictor = MatchPredictor()
    
    # Get team names from user
    team1_name = input("Enter first team name: ")
    team2_name = input("Enter second team name: ")
    
    # Get and display predictions
    predictions = predictor.get_predictions(team1_name, team2_name)
    print("\nPredictions:")
    print("=" * 50)
    print(predictions)

if __name__ == "__main__":
    main() 