import requests
from datetime import datetime, timedelta

def fetch_upcoming_matches(competition_id, api_key):
    # API endpoint and headers
    base_url = f"http://api.football-data.org/v4/competitions/{competition_id}/matches"
    headers = {
        "X-Auth-Token": api_key
    }
    
    # Date range: Today to 30 days in the future (more reasonable window)
    today = datetime.today()
    future_date = today + timedelta(days=30)
    
    # Query parameters
    params = {
        "dateFrom": today.strftime('%Y-%m-%d'),
        "dateTo": future_date.strftime('%Y-%m-%d'),
        "status": "SCHEDULED"  # Only get scheduled matches
    }
    
    print(f"\nQuerying matches from {params['dateFrom']} to {params['dateTo']}")
    
    try:
        # API request
        response = requests.get(base_url, headers=headers, params=params)
        
        # Handle common API errors
        if response.status_code == 403:
            print("\nAPI Error: Authentication failed. Please check your API key.")
            print("Note: Some competitions might require a premium subscription.")
            return []
        elif response.status_code == 429:
            print("\nAPI Error: Rate limit exceeded. Please try again later.")
            return []
        
        response.raise_for_status()  # Raise an error for other status codes
        
        # Process matches
        data = response.json()
        
        # Debug API response
        if 'error' in data:
            error_msg = data.get('message', data['error'])
            print(f"\nAPI Error: {error_msg}")
            if 'subscription' in error_msg.lower():
                print("Note: This competition might require a premium subscription.")
            return []
            
        matches = data.get("matches", [])
        competition_name = data.get("competition", {}).get("name", "Unknown")
        
        print(f"\nAPI Response Summary:")
        print(f"Competition: {competition_name}")
        print(f"Total matches found: {len(matches)}")
        print(f"Date range: {params['dateFrom']} to {params['dateTo']}")
        
        if not matches:
            print("No upcoming matches found in this date range.")
            return []
            
        return matches
    
    except requests.exceptions.RequestException as e:
        print(f"\nAPI Request Error: {str(e)}")
        if "Max retries exceeded" in str(e):
            print("Note: Please check your internet connection.")
        return []
    except ValueError as e:
        print(f"\nJSON Parsing Error: {str(e)}")
        print("Note: The API response was not in the expected format.")
        return []
    except Exception as e:
        print(f"\nUnexpected Error: {str(e)}")
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
