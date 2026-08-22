import os
import json
import hashlib
from datetime import datetime, timezone

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from jobspy import scrape_jobs


# ============================================================
# GOOGLE SHEETS
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets"
]

credentials = Credentials.from_service_account_info(
    json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"]),
    scopes=SCOPES
)

client = gspread.authorize(credentials)

spreadsheet = client.open_by_key(
    os.environ["GOOGLE_SHEET_ID"]
)

worksheet = spreadsheet.sheet1


# ============================================================
# SEARCH CONFIGURATION
# ============================================================

SEARCH_TERMS = [

    # -------------------------
    # Group A: Core AI / ML
    # -------------------------

    "machine learning engineer",
    "machine learning intern",
    "machine learning trainee",
    "AI engineer",
    "AI intern",
    "AI trainee",
    "artificial intelligence engineer",
    "artificial intelligence intern",

    # -------------------------
    # Group B: Junior / Fresher
    # -------------------------

    "junior machine learning engineer",
    "junior AI engineer",
    "graduate machine learning engineer",
    "graduate AI engineer",
    "entry level machine learning",
    "entry level AI engineer",
    "ML engineer fresher",
    "AI engineer fresher",

    # -------------------------
    # Group C: Research
    # -------------------------

    "AI research assistant",
    "machine learning research assistant",
    "AI research intern",
    "machine learning research intern",
    "research intern AI",
]


# Only these job sources for Stage 1.
# We will handle Facebook separately in Stage 2.
SITES = [
    "linkedin",
    "indeed",
    "google"
]


LOCATION = "Dhaka, Bangladesh"

RESULTS_PER_SEARCH = 15

HOURS_OLD = 168  # 7 days


# ============================================================
# TITLE FILTER
# ============================================================

# Words that indicate the job is relevant.
TARGET_KEYWORDS = [

    "machine learning",
    "machine-learning",
    "ml engineer",

    "artificial intelligence",
    "artificial-intelligence",
    "ai engineer",

    "ai intern",
    "ml intern",

    "ai trainee",
    "ml trainee",

    "ai research",
    "ml research",

    "research assistant",

    "research intern",

    "computer vision",
    "deep learning",

    "nlp",
    "natural language processing",

]


# Words that indicate the job is too senior or managerial.
EXCLUDED_KEYWORDS = [

    "senior",
    "sr.",
    "sr ",
    "lead",
    "principal",
    "staff engineer",

    "manager",
    "management",

    "director",
    "head of",

    "architect",

    "vice president",
    "vp ",

]


# Words that are good signs for a fresher.
FRESHER_KEYWORDS = [

    "intern",
    "internship",
    "trainee",

    "junior",
    "entry level",
    "entry-level",

    "graduate",
    "fresher",

    "new grad",
    "new graduate",

    "research assistant",
    "research intern",

]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_text(value):
    """Convert NaN/None to an empty string."""

    if value is None:
        return ""

    if pd.isna(value):
        return ""

    return str(value).strip()


def create_job_id(row):
    """
    Create a stable unique ID.

    Priority:
    1. Job URL
    2. Title + company + location
    """

    job_url = clean_text(row.get("job_url"))

    if job_url:
        unique_string = job_url.lower()

    else:
        unique_string = "|".join([
            clean_text(row.get("title")).lower(),
            clean_text(row.get("company")).lower(),
            clean_text(row.get("location")).lower(),
        ])

    return hashlib.sha256(
        unique_string.encode("utf-8")
    ).hexdigest()[:16]


def is_relevant_title(title):
    """
    Keep only AI/ML-related positions.
    """

    title = clean_text(title).lower()

    if not title:
        return False

    # First check whether the title contains
    # something AI/ML related.
    has_target_keyword = any(
        keyword in title
        for keyword in TARGET_KEYWORDS
    )

    if not has_target_keyword:
        return False

    # Then remove senior/managerial positions.
    has_excluded_keyword = any(
        keyword in title
        for keyword in EXCLUDED_KEYWORDS
    )

    if has_excluded_keyword:
        return False

    return True


def classify_fresher_friendliness(title):
    """
    Determine whether the position appears suitable
    for a fresh graduate.
    """

    title = clean_text(title).lower()

    if any(keyword in title for keyword in FRESHER_KEYWORDS):
        return "YES"

    return "MAYBE"


def relevance_score(title):
    """
    Simple Stage-1 relevance score.

    AI/ML title gets a high score.
    Fresher-related titles get additional points.
    """

    title = clean_text(title).lower()

    score = 0

    # Core AI/ML
    if "machine learning" in title:
        score += 50

    if "artificial intelligence" in title:
        score += 50

    if "ai engineer" in title:
        score += 50

    if "ml engineer" in title:
        score += 50

    # Related AI fields
    if "deep learning" in title:
        score += 40

    if "computer vision" in title:
        score += 40

    if "nlp" in title:
        score += 40

    # Research
    if "research" in title:
        score += 20

    # Fresher friendly
    if any(
        keyword in title
        for keyword in FRESHER_KEYWORDS
    ):
        score += 30

    return min(score, 100)


# ============================================================
# SEARCH
# ============================================================

print("=" * 60)
print("AI / ML JOB HUNTER")
print("=" * 60)

print(f"Location: {LOCATION}")
print(f"Search terms: {len(SEARCH_TERMS)}")
print(f"Sources: {', '.join(SITES)}")
print()


all_jobs = []


for index, search_term in enumerate(SEARCH_TERMS, start=1):

    print(
        f"[{index}/{len(SEARCH_TERMS)}] "
        f"Searching: {search_term}"
    )

    try:

        jobs = scrape_jobs(

            site_name=SITES,

            search_term=search_term,

            location=LOCATION,

            results_wanted=RESULTS_PER_SEARCH,

            hours_old=HOURS_OLD,

            verbose=0,

        )

        if jobs is not None and not jobs.empty:

            print(
                f"    Found {len(jobs)} raw results"
            )

            jobs["search_term"] = search_term

            all_jobs.append(jobs)

        else:

            print("    No results")

    except Exception as e:

        print(
            f"    Search failed: {search_term}"
        )

        print(
            f"    Reason: {e}"
        )

        # IMPORTANT:
        # One failed search should not kill
        # the entire workflow.
        continue


# ============================================================
# COMBINE SEARCH RESULTS
# ============================================================

if not all_jobs:

    print("\nNo jobs were collected.")
    raise SystemExit(0)


jobs = pd.concat(
    all_jobs,
    ignore_index=True
)

print()
print(
    f"Total raw jobs collected: {len(jobs)}"
)


# ============================================================
# REMOVE DUPLICATES FROM THIS RUN
# ============================================================

jobs["job_id"] = jobs.apply(
    create_job_id,
    axis=1
)

before_dedup = len(jobs)

jobs = jobs.drop_duplicates(
    subset=["job_id"]
)

print(
    f"Duplicates removed: "
    f"{before_dedup - len(jobs)}"
)

print(
    f"Unique jobs: {len(jobs)}"
)


# ============================================================
# AI / ML TITLE FILTER
# ============================================================

before_filter = len(jobs)

jobs = jobs[
    jobs["title"].apply(is_relevant_title)
].copy()

print(
    f"Non-AI/ML jobs removed: "
    f"{before_filter - len(jobs)}"
)

print(
    f"Relevant AI/ML jobs: {len(jobs)}"
)


# ============================================================
# ADD SCORES
# ============================================================

jobs["fresher_friendly"] = jobs[
    "title"
].apply(
    classify_fresher_friendliness
)

jobs["ai_ml_relevance"] = jobs[
    "title"
].apply(
    relevance_score
)


# ============================================================
# SORT BEST JOBS FIRST
# ============================================================

jobs = jobs.sort_values(
    by=[
        "fresher_friendly",
        "ai_ml_relevance"
    ],
    ascending=[
        True,
        False
    ]
)


# ============================================================
# READ EXISTING GOOGLE SHEET
# ============================================================

existing_rows = worksheet.get_all_values()

existing_ids = set()

if len(existing_rows) > 1:

    for row in existing_rows[1:]:

        if row:

            existing_ids.add(
                row[0]
            )


print(
    f"Existing jobs in Google Sheet: "
    f"{len(existing_ids)}"
)


# ============================================================
# PREPARE NEW JOBS
# ============================================================

new_rows = []

seen_this_run = set()

found_date = datetime.now(
    timezone.utc
).strftime(
    "%Y-%m-%d %H:%M UTC"
)


for _, job in jobs.iterrows():

    job_id = clean_text(
        job.get("job_id")
    )

    # Already in Google Sheets
    if job_id in existing_ids:
        continue

    # Duplicate within this run
    if job_id in seen_this_run:
        continue

    seen_this_run.add(job_id)

    title = clean_text(
        job.get("title")
    )

    company = clean_text(
        job.get("company")
    )

    location = clean_text(
        job.get("location")
    )

    date_posted = clean_text(
        job.get("date_posted")
    )

    job_url = clean_text(
        job.get("job_url")
    )

    source = clean_text(
        job.get("site")
    )

    job_type = clean_text(
        job.get("job_type")
    )

    fresher = clean_text(
        job.get("fresher_friendly")
    )

    relevance = clean_text(
        job.get("ai_ml_relevance")
    )

    search_term = clean_text(
        job.get("search_term")
    )

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
        "To Apply",

        # New fields
        fresher,
        relevance,
        search_term,

    ])


# ============================================================
# WRITE TO GOOGLE SHEETS
# ============================================================

if new_rows:

    worksheet.append_rows(
        new_rows,
        value_input_option="USER_ENTERED"
    )

    print()
    print(
        f"Added {len(new_rows)} NEW jobs "
        f"to Google Sheets."
    )

else:

    print()
    print(
        "No new jobs found."
    )


print()
print("=" * 60)
print("SEARCH COMPLETED")
print("=" * 60)
