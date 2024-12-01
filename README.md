# Football Match Predictor

A Python tool that predicts football match outcomes using historical data and AI analysis.

## Setup

1. Install requirements:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```
OPENAI_API_KEY=your_openai_api_key
FOOTBALL_DATA_API_KEY=your_football_data_api_key
```

## Usage

Run the predictor:
```bash
python match_predictor.py
```

1. Select a league from the available options
2. View predictions for matches in batches of 3
3. Choose to continue or stop after each batch

Available leagues (Free Tier):
- Premier League
- La Liga
- Bundesliga
- Serie A
- Ligue 1
- Eredivisie
- Championship
- Primeira Liga
- Champions League
- World Cup
- European Championship
- Brasileirão Serie A

## How It Works

1. **League Selection**:
   - Choose a league from the available options
   - Fuzzy matching handles misspellings and suggests corrections

2. **Data Collection**:
   - Fetches all teams in the selected league
   - Gets upcoming fixtures for the next 30 days
   - Retrieves historical data for teams involved

3. **Prediction Process**:
   - Analyzes each match using:
     - Recent team form
     - Head-to-head history
     - Historical performance data
   - Uses GPT-4 to generate predictions based on the data

4. **Output**:
   - Shows 3 matches at a time
   - For each match:
     - Match details (teams, date, time)
     - 3 specific predictions
     - Confidence levels based on historical data

## Example Output

```
Match: Chelsea vs Manchester United (December 01, 2024 at 13:30 UTC)
Predictions:
- Chelsea to win based on recent form
- Over 2.5 goals to be scored
- Both teams likely to score
-------------------------------------------------- 