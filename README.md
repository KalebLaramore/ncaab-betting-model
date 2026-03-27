# Sports Betting Analytics Model (Model v21)

This project is a Python-based sports analytics model that combines advanced basketball efficiency metrics with live sportsbook odds to identify value betting opportunities.

## Overview

The model integrates data from Torvik (college basketball analytics) with real-time odds from The Odds API. It processes, cleans, and matches data across sources to evaluate discrepancies between projected outcomes and sportsbook lines.

## Key Features

* Combines Torvik efficiency metrics with live odds data
* Uses fuzzy matching to align team names across different data sources
* Identifies value opportunities for spreads, moneyline, and totals
* Applies customizable filters based on probability and edge thresholds
* Handles real-world data inconsistencies and missing values

## Technologies Used

* Python (Pandas, Requests, BeautifulSoup)
* RapidFuzz (fuzzy string matching)
* The Odds API
* Data cleaning and transformation techniques

## How It Works

1. Load Torvik projections from saved HTML files
2. Pull live sportsbook odds using The Odds API
3. Match teams across datasets using fuzzy matching
4. Calculate projected spreads, totals, and probabilities
5. Identify betting opportunities where model projections differ from sportsbook lines

## Daily Usage

To run the model each day:

1. Go to the Torvik schedule page: https://barttorvik.com/trank.php
2. Navigate to the current day’s matchups
3. Save the page locally (Ctrl + S)

   * Save as: `torvik_schedule_today.html`
   * Place the file in the project folder
4. Run the script: `model_v21.py`

The model will process the data and output qualifying betting opportunities.

## Project Structure

* `model_v21.py` — main model script
* `torvik_schedule_today.html` — daily saved Torvik data
* `torvik_schedule_tomorrow.html` — optional next-day slate
* `requirements.txt` — required Python libraries

## Notes

* API keys are not included for security reasons
* Users must provide their own Odds API key using environment variables
* Torvik data must be manually saved daily due to lack of a public API

## Future Improvements

* Automate Torvik data scraping
* Export results to CSV or dashboard
* Improve model evaluation and tracking performance over time
