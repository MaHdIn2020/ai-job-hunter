import os
import json
import hashlib
import requests
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
# STAGE 1 CONFIGURATION
# ============================================================

SEARCH_TERMS = [

    # Core AI / ML
    "machine learning engineer",
    "machine learning intern",
    "machine learning trainee",
    "AI engineer",
    "AI intern",
    "AI trainee",
    "artificial intelligence engineer",
    "artificial intelligence intern",

    # Junior / Fresher
    "junior machine learning engineer",
    "junior AI engineer",
    "graduate machine learning engineer",
    "graduate AI engineer",
    "entry level machine learning",
    "entry level AI engineer",
    "ML engineer fresher",
    "AI engineer fresher",

    # Research
    "AI research assistant",
    "machine learning research assistant",
    "AI research intern",
    "machine learning research intern",
    "research intern AI",
]

SITES = [
    "linkedin",
    "indeed",
    "google"
]

LOCATION = "Dhaka, Bangladesh"

RESULTS_PER_SEARCH = 15

HOURS_OLD = 168


# ============================================================
# STAGE 2 FACEBOOK CONFIGURATION
# ============================================================

FACEBOOK_QUERIES = [

    # Core AI / ML
    'site:facebook.com "AI Engineer" "Dhaka"',
    'site:facebook.com "Machine Learning Engineer" "Dhaka"',
    'site:facebook.com "Artificial Intelligence Engineer" "Dhaka"',

    # Intern / Trainee
    'site:facebook.com "AI Intern" "Dhaka"',
    'site:facebook.com "Machine Learning Intern" "Dhaka"',
    'site:facebook.com "AI Trainee" "Dhaka"',
    'site:facebook.com "Machine Learning Trainee" "Bangladesh"',

    # Research
    'site:facebook.com "AI Research Intern" Bangladesh',
    'site:facebook.com "Machine Learning Research Intern" Bangladesh',
    'site:facebook.com "AI Research Assistant" Bangladesh',

    # Facebook groups
    'site:facebook.com/groups "AI jobs" Bangladesh',
    'site:facebook.com/groups "machine learning jobs" Bangladesh',
    'site:facebook.com/groups "AI internship" Bangladesh',
]


# ============================================================
# FILTER CONFIGURATION
# ============================================================

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
# GENERAL HELPERS
# ============================================================

def clean_text(value):

    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except:
        pass

    return str(value).strip()


def create_job_id(row):

    job_url = clean_text(
        row.get("job_url")
    )

    if job_url:

        unique_string = job_url.lower()

    else:

        unique_string = "|".join([
            clean_text(
                row.get("title")
            ).lower(),

            clean_text(
                row.get("company")
            ).lower(),

            clean_text(
                row.get("location")
            ).lower(),
        ])

    return hashlib.sha256(
        unique_string.encode("utf-8")
    ).hexdigest()[:16]


def is_relevant_title(title):

    title = clean_text(title).lower()

    if not title:
        return False

    has_target = any(
        keyword in title
        for keyword in TARGET_KEYWORDS
    )

    if not has_target:
        return False

    has_excluded = any(
        keyword in title
        for keyword in EXCLUDED_KEYWORDS
    )

    if has_excluded:
        return False

    return True


def classify_fresher_friendliness(title):

    title = clean_text(title).lower()

    if any(
        keyword in title
        for keyword in FRESHER_KEYWORDS
    ):
        return "YES"

    return "MAYBE"


def relevance_score(title):

    title = clean_text(title).lower()

    score = 0

    if "machine learning" in title:
        score += 50

    if "artificial intelligence" in title:
        score += 50

    if "ai engineer" in title:
        score += 50

    if "ml engineer" in title:
        score += 50

    if "deep learning" in title:
        score += 40

    if "computer vision" in title:
        score += 40

    if "nlp" in title:
        score += 40

    if "research" in title:
        score += 20

    if any(
        keyword in title
        for keyword in FRESHER_KEYWORDS
    ):
        score += 30

    return min(score, 100)


# ============================================================
# STAGE 1
# JOB BOARD SEARCH
# ============================================================

print("=" * 70)
print("AI JOB HUNTER")
print("=" * 70)

print()
print("STAGE 1: Job boards")
print("-" * 70)

all_jobs = []

for index, search_term in enumerate(
    SEARCH_TERMS,
    start=1
):

    print(
        f"[{index}/{len(SEARCH_TERMS)}] "
        f"{search_term}"
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
                f"    Raw results: {len(jobs)}"
            )

            jobs["search_term"] = search_term
            jobs["source_type"] = "Job Board"

            all_jobs.append(jobs)

        else:

            print("    No results")

    except Exception as e:

        print(
            f"    Search failed: {e}"
        )

        continue


# ============================================================
# STAGE 2
# FACEBOOK DISCOVERY
# ============================================================

print()
print("STAGE 2: Facebook discovery")
print("-" * 70)


def search_facebook(query):

    api_key = os.environ.get(
        "SERPER_API_KEY"
    )

    if not api_key:

        print(
            "SERPER_API_KEY not found. "
            "Skipping Facebook."
        )

        return []

    url = "https://google.serper.dev/search"

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }

    payload = {
        "q": query,
        "gl": "bd",
        "hl": "en",
        "num": 10,
    }

    try:

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        return data.get(
            "organic",
            []
        )

    except Exception as e:

        print(
            f"    Facebook search failed: {e}"
        )

        return []


facebook_jobs = []


for index, query in enumerate(
    FACEBOOK_QUERIES,
    start=1
):

    print(
        f"[FB {index}/{len(FACEBOOK_QUERIES)}]"
    )

    print(
        f"    {query}"
    )

    results = search_facebook(
        query
    )

    print(
        f"    Search results: {len(results)}"
    )

    for result in results:

        title = clean_text(
            result.get("title")
        )

        link = clean_text(
            result.get("link")
        )

        snippet = clean_text(
            result.get("snippet")
        )

        # Only Facebook results
        if "facebook.com" not in link.lower():
            continue

        # Create a temporary job object
        # so our existing filters can work.
        facebook_job = {

            "title": title,

            "company": "",

            "location": "Dhaka, Bangladesh",

            "date_posted": "",

            "job_url": link,

            "site": "Facebook",

            "job_type": "",

            "search_term": query,

            "snippet": snippet,

            "source_type": "Facebook",

        }

        # Apply the SAME AI/ML filter
        if not is_relevant_title(title):

            # Search snippets sometimes contain
            # the relevant job title rather than
            # the result title.
            combined_text = (
                title + " " + snippet
            ).lower()

            has_target = any(
                keyword in combined_text
                for keyword in TARGET_KEYWORDS
            )

            has_excluded = any(
                keyword in combined_text
                for keyword in EXCLUDED_KEYWORDS
            )

            if not has_target or has_excluded:

                continue

        facebook_jobs.append(
            facebook_job
        )


print()
print(
    f"Facebook relevant results: "
    f"{len(facebook_jobs)}"
)


# ============================================================
# CONVERT FACEBOOK RESULTS TO DATAFRAME
# ============================================================

if facebook_jobs:

    facebook_df = pd.DataFrame(
        facebook_jobs
    )

    all_jobs.append(
        facebook_df
    )


# ============================================================
# COMBINE EVERYTHING
# ============================================================

if not all_jobs:

    print()
    print("No jobs collected.")

    raise SystemExit(0)


jobs = pd.concat(
    all_jobs,
    ignore_index=True
)


print()
print(
    f"Total collected from all sources: "
    f"{len(jobs)}"
)


# ============================================================
# CREATE JOB IDs
# ============================================================

jobs["job_id"] = jobs.apply(
    create_job_id,
    axis=1
)


# ============================================================
# REMOVE DUPLICATES
# ============================================================

before = len(jobs)

jobs = jobs.drop_duplicates(
    subset=["job_id"]
)

print(
    f"Duplicates removed: "
    f"{before - len(jobs)}"
)


# ============================================================
# APPLY AI/ML FILTER TO JOB BOARD RESULTS
# ============================================================

before_filter = len(jobs)

jobs = jobs[
    jobs["title"].apply(
        is_relevant_title
    )
].copy()


print(
    f"Non-AI/ML jobs removed: "
    f"{before_filter - len(jobs)}"
)


# ============================================================
# ADD CLASSIFICATION
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
# SORT
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
# READ GOOGLE SHEET
# ============================================================

existing_rows = worksheet.get_all_values()

existing_ids = set()

if len(existing_rows) > 1:

    for row in existing_rows[1:]:

        if row:

            existing_ids.add(
                row[0]
            )


print()
print(
    f"Existing jobs in Sheet: "
    f"{len(existing_ids)}"
)


# ============================================================
# PREPARE NEW ROWS
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

    if job_id in existing_ids:
        continue

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
        f"NEW jobs added: "
        f"{len(new_rows)}"
    )

else:

    print()
    print(
        "No new jobs found."
    )


print()
print("=" * 70)
print("JOB HUNTER COMPLETED")
print("=" * 70)
