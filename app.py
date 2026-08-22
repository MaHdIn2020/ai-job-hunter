import os
import hashlib
from datetime import datetime, timezone

import gspread
from google.oauth2.service_account import Credentials
from jobspy import scrape_jobs


# =========================
# Google Sheets configuration
# =========================

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets"
]

credentials = Credentials.from_service_account_info(
    os.environ["GOOGLE_CREDENTIALS_JSON"],
    scopes=SCOPES
)

client = gspread.authorize(credentials)

spreadsheet = client.open_by_key(
    os.environ["GOOGLE_SHEET_ID"]
)

worksheet = spreadsheet.sheet1


# =========================
# Scrape jobs
# =========================

print("Starting job search...")

jobs = scrape_jobs(
    site_name=["linkedin", "indeed", "google"],
    search_term="machine learning engineer",
    location="Dhaka",
    results_wanted=20,
    hours_old=72
)

print(f"Found {len(jobs)} jobs")


# =========================
# Create unique Job ID
# =========================

def create_job_id(row):
    """
    Create a stable ID using the job URL.
    If URL doesn't exist, use title + company + location.
    """

    job_url = str(row.get("job_url", "")).strip()

    if job_url:
        unique_string = job_url
    else:
        unique_string = "|".join([
            str(row.get("title", "")).strip().lower(),
            str(row.get("company", "")).strip().lower(),
            str(row.get("location", "")).strip().lower()
        ])

    return hashlib.sha256(
        unique_string.encode("utf-8")
    ).hexdigest()[:16]


# =========================
# Read existing jobs
# =========================

existing_rows = worksheet.get_all_values()

existing_ids = set()

if len(existing_rows) > 1:
    for row in existing_rows[1:]:
        if row:
            existing_ids.add(row[0])


print(f"Existing jobs in sheet: {len(existing_ids)}")


# =========================
# Prepare new jobs
# =========================

new_rows = []
seen_this_run = set()

found_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

for _, job in jobs.iterrows():

    job_id = create_job_id(job)

    # Duplicate already in Google Sheet
    if job_id in existing_ids:
        continue

    # Duplicate within current scraping result
    if job_id in seen_this_run:
        continue

    seen_this_run.add(job_id)

    title = str(job.get("title", ""))
    company = str(job.get("company", ""))
    location = str(job.get("location", ""))
    date_posted = str(job.get("date_posted", ""))
    job_url = str(job.get("job_url", ""))
    source = str(job.get("site", ""))
    job_type = str(job.get("job_type", ""))

    new_rows.append([
        job_id,
        title,
        company,
        location,
        date_posted,
        job_url,
        source,
        job_type,
        found_date,
        "To Apply"
    ])


# =========================
# Add new jobs to Sheet
# =========================

if new_rows:

    worksheet.append_rows(
        new_rows,
        value_input_option="USER_ENTERED"
    )

    print(f"Added {len(new_rows)} new jobs.")

else:

    print("No new jobs found.")


print("Job search completed.")
