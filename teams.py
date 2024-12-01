import requests

def get_teams(league_code, api_token):
    """
    Fetches team IDs and names for a given league from the Football Data API.
    
    Args:
    league_code (str): The code of the league (e.g., 'PL' for Premier League).
    api_token (str): Your Football Data API token.
    
    Returns:
    list: A list of dictionaries with team IDs and names.
    """
    url = f"https://api.football-data.org/v4/competitions/{league_code}/teams"
    headers = {
        "X-Auth-Token": api_token
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        teams = [
            {"id": team["id"], "name": team["name"]} 
            for team in data.get("teams", [])
        ]
        return teams
    else:
        print(f"Error: Unable to fetch data. Status code: {response.status_code}")
        print(response.json())
        return []

if __name__ == "__main__":
    # Replace with your actual API token and league code
    API_TOKEN = "deb1d19bdcfd48a29d2cf9a23093d407"
    LEAGUE_CODE = "PL"  # Example: 'PL' for Premier League
    
    teams = get_teams(LEAGUE_CODE, API_TOKEN)
    
    if teams:
        print(f"Teams in league {LEAGUE_CODE}:")
        for team in teams:
            print(f"{team['id']}: {team['name']}")