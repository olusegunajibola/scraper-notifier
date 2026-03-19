# Scraper Notifier (`scraper.py`)

`scraper.py` checks a list of official regional websites, searches each page for target keywords, and sends an email alert when a match is found.

## What the script does

1. Loads email credentials and settings from `.env`.
2. Reads rows from `Elenco USR trial.csv`.
3. For each row:
   - Fetches the site URL.
   - Extracts page text with BeautifulSoup.
   - Compares page content against comma-separated keywords.
4. Sends an email alert if any keyword matches.
5. Saves processed entries to `sent_notifications.txt` to avoid duplicate alerts.
6. Writes timestamped run logs to `run_log.txt`.

## Requirements

- Python 3.8+
- `pip` (or Conda)
- Internet access to target websites
- A Gmail account with an app password (for SMTP)

## Install dependencies

Using `pip`:

```bash
pip install -r requirements.txt
```

Or with Conda:

```bash
conda env create -f environment.yaml
conda activate scraper-notifier
```

## Environment variables

Create a `.env` file in the project root:

```env
SENDER_EMAIL=your_email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password # create password using google app passwords i.e https://myaccount.google.com/apppasswords?
RECEIVER_EMAIL=recipient_email@example.com
```

Notes:
- `SENDER_EMAIL`: Gmail address used to send alerts.
- `EMAIL_PASSWORD`: Gmail app password (not your normal login password).
- `RECEIVER_EMAIL`: Destination email for notifications.

## CSV input format

The script expects `Elenco USR trial.csv` with these columns:

- `Regione`
- `Sito Web Ufficiale`
- `Keywords`

Example row:

```csv
Regione,Sito Web Ufficiale,Keywords
Lazio,https://www.example.gov.it,"concorso,graduatoria,nomina"
```

## Run the script

```bash
python scraper.py
```

## Output files

- `sent_notifications.txt`: stores processed `<region>_<url>` IDs.
- `run_log.txt`: timestamped activity log.

## Behavior notes

- Uses a browser-like `User-Agent` and a `20s` request timeout.
- Waits `2s` between URL checks.
- Only sends one alert per `<region>_<url>` combination unless history is cleared.

## Resetting notification history

If you want to re-check and re-alert previous entries, clear:

- `sent_notifications.txt`

## Troubleshooting

- `FileNotFoundError` for CSV: ensure `Elenco USR trial.csv` exists in the project root.
- SMTP login failure: verify Gmail app password and account SMTP permissions.
- Empty matches: confirm keywords are lowercase-friendly terms and present in page text.


