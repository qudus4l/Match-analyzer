import requests
from datetime import datetime

def fetch_upcoming_matches(competition_id, api_key):
    # API endpoint and headers
    base_url = f"http://api.football-data.org/v4/competitions/{competition_id}/matches"
    headers = {
        "X-Auth-Token": api_key
    }
    
    # Today's date and a date range for the future
    today = datetime.today().strftime('%Y-%m-%d')
    future_date = (datetime.today().replace(year=datetime.today().year + 1)).strftime('%Y-%m-%d')
    
    # Query parameters
    params = {
        "dateFrom": today,
        "dateTo": future_date
    }
    
    try:
        # API request
        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()  # Raise an error for bad status codes
        
        # Process matches
        data = response.json()
        matches = data.get("matches", [])
        
        if not matches:
            print("No upcoming matches found.")
            return []
            
        return matches
    
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return []

# Example usage (only if run directly)
if __name__ == "__main__":
    competition_id = "2021"  # Premier League
    api_key = "deb1d19bdcfd48a29d2cf9a23093d407"
    
    matches = fetch_upcoming_matches(competition_id, api_key)
    if matches:
        print(f"Upcoming matches for competition {competition_id}:")
        for match in matches:
            home_team = match['homeTeam']['name']
            away_team = match['awayTeam']['name']
            match_date = match['utcDate']
            print(f"{home_team} vs {away_team} on {match_date}")
