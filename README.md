# YCombinator Company Scraper

This project consists of two Python scripts that utilize Selenium and Pandas to scrape and extract company and founder data from YCombinator website.

## Features

1. **Search and Scrape Company Links**  
   The first script searches for company names on the Y Combinator website and extracts their profile links:
   - Reads a list of company names from an Excel file.
   - Automates a search on YCombinator website using Selenium.
   - Collects and saves the profile links so we can obtain scrape company founder data.

2. **Extract Founder and Social Media Data**  
   The second script navigates through the extracted profile links to gather detailed information:
   - Extracts founder names, Twitter handles, and LinkedIn profiles.
   - Handles multiple founders for each company.

## Requirements

- Python 3.8+
- Google Chrome browser
- ChromeDriver (compatible with your Chrome version)
- Required Python libraries:
  - `selenium`
  - `pandas`
  - `openpyxl` (for Excel file handling)

## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/yc-data-scraper.git
   cd yc-data-scraper
2. **Install Dependencies**:
   ```bash
   pip install selenium pandas openpyxl

--- 
