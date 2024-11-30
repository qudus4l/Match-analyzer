import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
BASE_URL = 'http://api.football-data.org/v4'
FOOTBALL_API_KEY = os.getenv('FOOTBALL_DATA_API_KEY')
HEADERS = {'X-Auth-Token': FOOTBALL_API_KEY}

# Team ID mappings
TEAM_IDS = {
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

def get_team_id(team_name):
    """Get team ID with fuzzy matching fallback"""
    team_name_lower = team_name.lower()
    
    # Direct match
    if team_name_lower in TEAM_IDS:
        return TEAM_IDS[team_name_lower]
        
    # Partial match
    for known_name, team_id in TEAM_IDS.items():
        if team_name_lower in known_name or known_name in team_name_lower:
            return team_id
            
    # Fallback to API search if still no match
    url = f"{BASE_URL}/teams"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        teams = response.json()['teams']
        for team in teams:
            if team_name.lower() in team['name'].lower():
                return team['id']
    return None

def get_team_matches(team_id, days_back=90):
    """Get detailed match history for a team"""
    date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    date_to = datetime.now().strftime('%Y-%m-%d')
    
    url = f"{BASE_URL}/teams/{team_id}/matches"
    params = {
        'dateFrom': date_from,
        'dateTo': date_to,
        'status': 'FINISHED'
    }
    
    response = requests.get(url, headers=HEADERS, params=params)
    
    if response.status_code == 200:
        matches = response.json()['matches']
        match_history = []
        
        for match in matches:
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
                'result': get_result(match, team_id)
            }
            match_history.append(match_info)
            
        return match_history
    return []

def get_result(match, team_id):
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

def get_head_to_head(team1_id, team2_id):
    """Get head to head matches between two teams"""
    url = f"{BASE_URL}/teams/{team1_id}/matches"
    params = {
        'status': 'FINISHED',
        'limit': 200
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        
        matches = response.json()['matches']
        match_id = None
        
        # Find a match between these two teams
        for match in matches:
            if (match['homeTeam'].get('id') == team2_id or 
                match['awayTeam'].get('id') == team2_id):
                match_id = match['id']
                break
        
        if not match_id:
            return None
        
        # Get head to head data using the match ID
        url = f"{BASE_URL}/matches/{match_id}/head2head"
        params = {'limit': 60}
        
        response = requests.get(url, headers=HEADERS, params=params)
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
            'draws': agg['homeTeam']['draws']
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

def fetch_upcoming_matches(competition_id="2021"):
    """Fetch upcoming matches for a competition"""
    base_url = f"{BASE_URL}/competitions/{competition_id}/matches"
    
    # Today's date and a date range for the future
    today = datetime.today().strftime('%Y-%m-%d')
    future_date = (datetime.today().replace(year=datetime.today().year + 1)).strftime('%Y-%m-%d')
    
    params = {
        "dateFrom": today,
        "dateTo": future_date
    }
    
    try:
        response = requests.get(base_url, headers=HEADERS, params=params)
        response.raise_for_status()
        
        data = response.json()
        matches = data.get("matches", [])
        
        if not matches:
            return []
            
        upcoming_matches = []
        for match in matches:
            match_info = {
                'home_team': match['homeTeam']['name'],
                'away_team': match['awayTeam']['name'],
                'date': match['utcDate']
            }
            upcoming_matches.append(match_info)
            
        return upcoming_matches
    
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return [] 