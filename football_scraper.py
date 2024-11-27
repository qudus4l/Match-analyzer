from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import re
from datetime import datetime

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run Chrome in headless mode
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        return driver
    except Exception as e:
        print("Error setting up Chrome webdriver:", str(e))
        exit(1)

def parse_head_to_head_data(raw_data):
    lines = raw_data.split('\n')
    matches = []
    competition = ''
    i = 0
    
    # Define a list of known competitions
    known_competitions = ['Premier League', 'FA Cup', 'EFL Cup', 'UEFA Champions League', 'Community Shield']
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip irrelevant lines
        if line in ['Head-to-Head', 'At Manchester United', 'This Tournament', 'Sofascore Ratings']:
            i += 1
            continue
        
        # Check if the line indicates a competition
        if line in known_competitions:
            competition = line
            i += 1
            continue
        
        # Check for date pattern (dd/mm/yy)
        date_match = re.match(r'\d{2}/\d{2}/\d{2}', line)
        if date_match:
            date_str = line
            try:
                date_obj = datetime.strptime(date_str, '%d/%m/%y')
                # **Modification starts here**
                # Skip matches before 2020
                if date_obj.year < 2020:
                    break  # Exit the loop as we've reached matches before 2020
                date = date_obj.strftime('%d/%m/%y')
                # **Modification ends here**
            except ValueError:
                # If date format is incorrect, skip this line
                i += 1
                continue
            
            i += 1
            # Check for match status (FT, AP, Postponed, 15:00)
            status = lines[i].strip()
            if status in ['FT', 'AP', 'Postponed', '15:00']:
                match_status = status
                i += 1
            else:
                match_status = ''
            
            # Get home and away teams
            if i + 1 < len(lines):
                home_team = lines[i].strip()
                away_team = lines[i+1].strip()
                i += 2
            else:
                break  # Not enough lines to parse teams
            
            # Initialize scores and ratings
            home_goals = ''
            away_goals = ''
            home_rating = ''
            away_rating = ''
            
            # Get scores and ratings if available
            scores_collected = 0
            scores_and_ratings = []
            while i < len(lines) and scores_collected < 4:
                score_line = lines[i].strip()
                # Check if the line contains a number (could be score or rating)
                if re.match(r'^\d+(\s*\(\d+\))?$', score_line):
                    scores_and_ratings.append(score_line)
                    scores_collected += 1
                    i += 1
                else:
                    break  # No more scores/ratings available
            
            if len(scores_and_ratings) >= 4:
                home_goals = scores_and_ratings[0]
                home_rating = scores_and_ratings[1]
                away_goals = scores_and_ratings[2]
                away_rating = scores_and_ratings[3]
            elif len(scores_and_ratings) >= 2:
                home_goals = scores_and_ratings[0]
                away_goals = scores_and_ratings[1]
            else:
                # Handle cases where match is postponed or scores are not available
                home_goals = 'Postponed'
                away_goals = 'Postponed'
            
            match = {
                'date': date,
                'competition': competition,
                'home_team': home_team,
                'away_team': away_team,
                'home_goals': home_goals,
                'away_goals': away_goals,
                # 'home_rating': home_rating,  # Uncomment if you want to include ratings
                # 'away_rating': away_rating   # Uncomment if you want to include ratings
            }
            matches.append(match)
        else:
            i += 1  # Move to the next line if no date is found

    return matches

def get_head_to_head_data(team1, team2):
    driver = setup_driver()
    time.sleep(2)  # Wait for the driver to be ready
    
    try:
        # Go to Google and search
        driver.get("https://www.google.com")
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys(f"{team1} vs {team2} sofascore")
        search_box.send_keys(Keys.RETURN)
        time.sleep(2)
        
        # Click on the first result
        first_result = driver.find_element(By.CSS_SELECTOR, "div.g a")
        first_result.click()
        time.sleep(2)
        
        # Scroll to load content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)
        
        # Find the Head-to-Head section
        all_elements = driver.find_elements(By.CSS_SELECTOR, "*")
        for element in all_elements:
            text = element.text.strip()
            if text and "Head-to-Head" in text:
                start_index = text.index("Head-to-Head")
                raw_data = text[start_index:]
                # Remove any disclaimer or notes at the end
                if "*IMPORTANT NOTICE" in raw_data:
                    raw_data = raw_data.split("*IMPORTANT NOTICE")[0]
                return raw_data
            
        return "No Head-to-Head data found"
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return str(e)
    finally:
        driver.quit()

def save_matches_to_csv(matches, team1, team2):
    if matches:
        filename = f"{team1.lower()}_{team2.lower()}_h2h.csv".replace(" ", "_")
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            fieldnames = ['date', 'competition', 'home_team', 'away_team', 'home_goals', 'away_goals']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(matches)
        print(f"Data saved to {filename}")

def main():
    team1 = input("Enter first team name: ")
    team2 = input("Enter second team name: ")
    
    print("Fetching data...")
    raw_data = get_head_to_head_data(team1, team2)
    
    print("\nRaw Head-to-Head data:")
    print("-------------------------")
    print(raw_data)
    
    matches = parse_head_to_head_data(raw_data)
    
    # Display the matches in a table format
    from tabulate import tabulate
    
    table = []
    for match in matches:
        table.append([
            match['date'],
            match['competition'],
            match['home_team'],
            match['away_team'],
            match['home_goals'],
            match['away_goals']
        ])
    
    print("\nStructured Data (From 2020 onwards):")
    print(tabulate(table, headers=['Date', 'Competition', 'Home Team', 'Away Team', 'Home Goals', 'Away Goals']))
    
    # Save to CSV
    save_matches_to_csv(matches, team1, team2)
    
if __name__ == "__main__":
    main()
