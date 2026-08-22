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
# GOOGLE SHEETS CONFIGURATION
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets"
]


# Load Google credentials from GitHub Secret
credentials = Credentials.from_service_account_info(
    json.loads(
        os.environ["GOOGLE_CREDENTIALS_JSON"]
    ),
    scopes=SCOPES
)


# Connect to Google Sheets
client = gspread.authorize(credentials)

spreadsheet = client.open_by_key(
    os.environ["GOOGLE_SHEET_ID"]
)

worksheet = spreadsheet.sheet1


# ============================================================
# GENERAL CONFIGURATION
# ============================================================

LOCATION = "Dhaka, Bangladesh"

RESULTS_PER_SEARCH = 15

# JobSpy will search approximately the last 7 days
HOURS_OLD = 168


# ============================================================
# STAGE 1
# JOB BOARD SEARCH TERMS
# ============================================================

SEARCH_TERMS = [

    # --------------------------------------------------------
    # Machine Learning
    # --------------------------------------------------------

    "machine learning engineer",

    "machine learning intern",

    "machine learning trainee",

    "machine learning developer",

    "machine learning research intern",

    "machine learning research assistant",


    # --------------------------------------------------------
    # Artificial Intelligence
    # --------------------------------------------------------

    "AI engineer",

    "AI intern",

    "AI trainee",

    "AI developer",

    "artificial intelligence engineer",

    "artificial intelligence intern",

    "artificial intelligence trainee",


    # --------------------------------------------------------
    # Junior / Fresher
    # --------------------------------------------------------

    "junior AI engineer",

    "junior machine learning engineer",

    "entry level AI engineer",

    "entry level machine learning",

    "graduate AI engineer",

    "graduate machine learning engineer",

    "AI engineer fresher",

    "ML engineer fresher",


    # --------------------------------------------------------
    # Research
    # --------------------------------------------------------

    "AI research intern",

    "AI research assistant",

    "machine learning research intern",

    "machine learning research assistant",


    # --------------------------------------------------------
    # Related AI/ML Fields
    # --------------------------------------------------------

    "deep learning engineer",

    "deep learning intern",

    "computer vision engineer",

    "computer vision intern",

    "NLP engineer",

    "NLP intern",

    "natural language processing intern",

]


# JobSpy sources
SITES = [
    "linkedin",
    "indeed",
    "google",
]


# ============================================================
# STAGE 2
# FACEBOOK SEARCH QUERIES
# ============================================================

FACEBOOK_QUERIES = [

    # --------------------------------------------------------
    # AI Engineer
    # --------------------------------------------------------

    'site:facebook.com "AI Engineer" "Dhaka" hiring',

    'site:facebook.com "Artificial Intelligence Engineer" "Dhaka" hiring',

    'site:facebook.com "Machine Learning Engineer" "Dhaka" hiring',


    # --------------------------------------------------------
    # Internships
    # --------------------------------------------------------

    'site:facebook.com "AI Intern" "Dhaka" hiring',

    'site:facebook.com "Machine Learning Intern" "Dhaka" hiring',

    'site:facebook.com "Artificial Intelligence Intern" "Dhaka" hiring',


    # --------------------------------------------------------
    # Trainee / Junior
    # --------------------------------------------------------

    'site:facebook.com "AI Trainee" "Dhaka" hiring',

    'site:facebook.com "Machine Learning Trainee" Bangladesh hiring',

    'site:facebook.com "Junior AI Engineer" "Dhaka" hiring',

    'site:facebook.com "Junior Machine Learning" "Dhaka" hiring',


    # --------------------------------------------------------
    # Research
    # --------------------------------------------------------

    'site:facebook.com "AI Research Intern" Bangladesh',

    'site:facebook.com "Machine Learning Research Intern" Bangladesh',

    'site:facebook.com "AI Research Assistant" Bangladesh',


    # --------------------------------------------------------
    # Facebook Groups
    # --------------------------------------------------------

    'site:facebook.com/groups "AI jobs" Bangladesh',

    'site:facebook.com/groups "AI internship" Bangladesh',

    'site:facebook.com/groups "machine learning jobs" Bangladesh',

]


# ============================================================
# AI / ML TARGET KEYWORDS
# ============================================================

TARGET_KEYWORDS = [

    "machine learning",

    "machine-learning",

    "ml engineer",

    "ml intern",

    "ml trainee",

    "ml developer",

    "artificial intelligence",

    "artificial-intelligence",

    "ai engineer",

    "ai intern",

    "ai trainee",

    "ai developer",

    "ai research",

    "ml research",

    "deep learning",

    "deep-learning",

    "computer vision",

    "computer-vision",

    "natural language processing",

    "natural-language processing",

    "nlp",

]


# ============================================================
# EXCLUDED / SENIOR KEYWORDS
# ============================================================

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


# ============================================================
# FRESHER KEYWORDS
# ============================================================

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
# FACEBOOK JOB INDICATOR KEYWORDS
# ============================================================

FACEBOOK_JOB_KEYWORDS = [

    "hiring",

    "hire",

    "job",

    "jobs",

    "vacancy",

    "vacancies",

    "position",

    "opening",

    "openings",

    "recruiting",

    "recruitment",

    "apply",

    "application",

    "intern",

    "internship",

    "trainee",

    "engineer",

    "developer",

    "research",

]


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def clean_text(value):

    """
    Convert values safely to strings.
    """

    if value is None:

        return ""

    try:

        if pd.isna(value):

            return ""

    except Exception:

        pass

    return str(value).strip()


# ------------------------------------------------------------
# Create unique Job ID
# ------------------------------------------------------------


def create_job_id(row):

    """
    Create a stable unique ID.

    Priority:

    1. Job URL
    2. Job title + company + location
    """

    job_url = clean_text(
        row.get("job_url")
    )

    if job_url:

        unique_string = (
            job_url
            .lower()
            .strip()
        )

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

        unique_string.encode(
            "utf-8"
        )

    ).hexdigest()[:16]


# ------------------------------------------------------------
# AI/ML title relevance
# ------------------------------------------------------------


def is_relevant_title(title):

    """
    Return True if the title is AI/ML related
    and does not look like a senior position.
    """

    title = clean_text(
        title
    ).lower()


    if not title:

        return False


    # Must contain an AI/ML keyword
    has_target = any(

        keyword in title

        for keyword in TARGET_KEYWORDS

    )


    if not has_target:

        return False


    # Reject senior roles
    has_excluded = any(

        keyword in title

        for keyword in EXCLUDED_KEYWORDS

    )


    if has_excluded:

        return False


    return True


# ------------------------------------------------------------
# Fresher classification
# ------------------------------------------------------------


def classify_fresher_friendliness(title):

    title = clean_text(
        title
    ).lower()


    if any(

        keyword in title

        for keyword in FRESHER_KEYWORDS

    ):

        return "YES"


    return "MAYBE"


# ------------------------------------------------------------
# AI/ML relevance score
# ------------------------------------------------------------


def relevance_score(title):

    title = clean_text(
        title
    ).lower()


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


    return min(
        score,
        100
    )


# ============================================================
# FACEBOOK FUNCTIONS
# ============================================================


def search_facebook(query):

    """
    Search Google through Serper.

    qdr:m = approximately the last month.
    """

    api_key = os.environ.get(
        "SERPER_API_KEY"
    )


    if not api_key:

        print(
            "    ERROR: SERPER_API_KEY "
            "not found."
        )

        return []


    url = (
        "https://google.serper.dev/search"
    )


    headers = {

        "X-API-KEY":
            api_key,

        "Content-Type":
            "application/json",

    }


    payload = {

        "q": query,

        # Bangladesh
        "gl": "bd",

        # English
        "hl": "en",

        # Number of Google results
        "num": 10,

        # IMPORTANT:
        # Approximately last month
        "tbs": "qdr:m",

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
            f"    Serper error: {e}"
        )

        return []


# ------------------------------------------------------------
# Detect old years
# ------------------------------------------------------------


def contains_old_year(text):

    """
    Reject results that explicitly contain
    an old year.

    Example:

    "AI Engineer Job 2023"

    will be rejected.
    """

    text = clean_text(
        text
    )


    current_year = datetime.now(
        timezone.utc
    ).year


    for year in range(
        2018,
        current_year
    ):

        if str(year) in text:

            if year < current_year:

                return True


    return False


# ------------------------------------------------------------
# Facebook job relevance
# ------------------------------------------------------------


def is_facebook_job_result(
    title,
    snippet
):

    """
    Facebook results need to satisfy
    BOTH conditions:

    1. AI/ML related
    2. Looks like a job/hiring post
    """

    combined = (

        clean_text(title)
        + " "
        + clean_text(snippet)

    ).lower()


    # --------------------------------------------------------
    # AI/ML requirement
    # --------------------------------------------------------

    has_ai_ml = any(

        keyword in combined

        for keyword in TARGET_KEYWORDS

    )


    if not has_ai_ml:

        return False


    # --------------------------------------------------------
    # Job/hiring requirement
    # --------------------------------------------------------

    has_job_indicator = any(

        keyword in combined

        for keyword in FACEBOOK_JOB_KEYWORDS

    )


    if not has_job_indicator:

        return False


    # --------------------------------------------------------
    # Senior role exclusion
    # --------------------------------------------------------

    has_excluded = any(

        keyword in combined

        for keyword in EXCLUDED_KEYWORDS

    )


    if has_excluded:

        return False


    return True


# ============================================================
# MAIN PROGRAM
# ============================================================


print()
print("=" * 70)
print("AI JOB HUNTER")
print("=" * 70)
print()


# ============================================================
# STAGE 1
# JOB BOARDS
# ============================================================


print(
    "STAGE 1: Job boards"
)

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

            results_wanted=
                RESULTS_PER_SEARCH,

            hours_old=HOURS_OLD,

            verbose=0,

        )


        if (
            jobs is not None
            and not jobs.empty
        ):

            print(

                f"    Raw results: "
                f"{len(jobs)}"

            )


            jobs[
                "search_term"
            ] = search_term


            jobs[
                "source_type"
            ] = "Job Board"


            all_jobs.append(
                jobs
            )


        else:

            print(
                "    No results"
            )


    except Exception as e:

        print(

            f"    Search failed: "
            f"{e}"

        )

        continue


# ============================================================
# STAGE 2
# FACEBOOK
# ============================================================


print()

print(
    "STAGE 2: Facebook discovery"
)

print("-" * 70)


facebook_jobs = []


facebook_seen_urls = set()


for index, query in enumerate(

    FACEBOOK_QUERIES,

    start=1

):


    print()

    print(

        f"[FB {index}/"
        f"{len(FACEBOOK_QUERIES)}]"

    )


    print(
        f"    {query}"
    )


    results = search_facebook(
        query
    )


    print(

        f"    Search results: "
        f"{len(results)}"

    )


    for result in results:


        title = clean_text(

            result.get(
                "title"
            )

        )


        link = clean_text(

            result.get(
                "link"
            )

        )


        snippet = clean_text(

            result.get(
                "snippet"
            )

        )


        # ----------------------------------------------------
        # Facebook only
        # ----------------------------------------------------

        if (
            "facebook.com"
            not in link.lower()
        ):

            continue


        # ----------------------------------------------------
        # Avoid same URL
        # ----------------------------------------------------

        normalized_url = (
            link
            .lower()
            .strip()
        )


        if (
            normalized_url
            in facebook_seen_urls
        ):

            continue


        facebook_seen_urls.add(
            normalized_url
        )


        # ----------------------------------------------------
        # Reject obvious old years
        # ----------------------------------------------------

        combined_text = (

            title
            + " "
            + snippet

        )


        if contains_old_year(
            combined_text
        ):

            print(

                f"    SKIPPED OLD: "
                f"{title}"

            )

            continue


        # ----------------------------------------------------
        # AI/ML + job relevance
        # ----------------------------------------------------

        if not is_facebook_job_result(

            title,

            snippet

        ):

            continue


        # ----------------------------------------------------
        # Fresher classification
        # ----------------------------------------------------

        fresher_status = (

            classify_fresher_friendliness(

                title

            )

        )


        # ----------------------------------------------------
        # Relevance score
        # ----------------------------------------------------

        relevance = (

            relevance_score(
                title
            )

        )


        # ----------------------------------------------------
        # Save Facebook job
        # ----------------------------------------------------

        facebook_job = {

            "title":
                title,

            "company":
                "",

            "location":
                "Dhaka, Bangladesh",

            "date_posted":
                "",

            "job_url":
                link,

            "site":
                "Facebook",

            "job_type":
                "",

            "search_term":
                query,

            "snippet":
                snippet,

            "source_type":
                "Facebook",

            "fresher_friendly":
                fresher_status,

            "ai_ml_relevance":
                relevance,

        }


        facebook_jobs.append(
            facebook_job
        )


print()


print(

    f"Facebook relevant jobs: "
    f"{len(facebook_jobs)}"

)


# ============================================================
# FACEBOOK → DATAFRAME
# ============================================================


if facebook_jobs:

    facebook_df = pd.DataFrame(
        facebook_jobs
    )


    all_jobs.append(
        facebook_df
    )


# ============================================================
# CHECK IF ANY JOBS WERE FOUND
# ============================================================


if not all_jobs:

    print()

    print(
        "No jobs collected."
    )

    raise SystemExit(0)


# ============================================================
# COMBINE ALL SOURCES
# ============================================================


jobs = pd.concat(

    all_jobs,

    ignore_index=True

)


print()

print(

    f"Total collected from all "
    f"sources: {len(jobs)}"

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

    subset=[
        "job_id"
    ]

)


print(

    f"Duplicates removed: "
    f"{before - len(jobs)}"

)


# ============================================================
# AI/ML FILTER
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
# ENSURE CLASSIFICATION COLUMNS EXIST
# ============================================================


if (
    "fresher_friendly"
    not in jobs.columns
):

    jobs[
        "fresher_friendly"
    ] = ""


if (
    "ai_ml_relevance"
    not in jobs.columns
):

    jobs[
        "ai_ml_relevance"
    ] = ""


# ============================================================
# CLASSIFY FRESHER FRIENDLINESS
# ============================================================


jobs[
    "fresher_friendly"
] = jobs.apply(

    lambda row:

        row[
            "fresher_friendly"
        ]

        if clean_text(

            row[
                "fresher_friendly"
            ]

        )

        else classify_fresher_friendliness(

            row[
                "title"
            ]

        ),

    axis=1

)


# ============================================================
# CALCULATE RELEVANCE
# ============================================================


jobs[
    "ai_ml_relevance"
] = jobs.apply(

    lambda row:

        row[
            "ai_ml_relevance"
        ]

        if clean_text(

            row[
                "ai_ml_relevance"
            ]

        )

        else relevance_score(

            row[
                "title"
            ]

        ),

    axis=1

)


# ============================================================
# SORT RESULTS
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


existing_rows = (

    worksheet.get_all_values()

)


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

        job.get(
            "job_id"
        )

    )


    # Already in Google Sheet
    if job_id in existing_ids:

        continue


    # Duplicate during current run
    if job_id in seen_this_run:

        continue


    seen_this_run.add(
        job_id
    )


    # --------------------------------------------------------
    # Extract fields
    # --------------------------------------------------------

    title = clean_text(

        job.get(
            "title"
        )

    )


    company = clean_text(

        job.get(
            "company"
        )

    )


    location = clean_text(

        job.get(
            "location"
        )

    )


    date_posted = clean_text(

        job.get(
            "date_posted"
        )

    )


    job_url = clean_text(

        job.get(
            "job_url"
        )

    )


    source = clean_text(

        job.get(
            "site"
        )

    )


    job_type = clean_text(

        job.get(
            "job_type"
        )

    )


    fresher = clean_text(

        job.get(
            "fresher_friendly"
        )

    )


    relevance = clean_text(

        job.get(
            "ai_ml_relevance"
        )

    )


    search_term = clean_text(

        job.get(
            "search_term"
        )

    )


    # --------------------------------------------------------
    # Google Sheet row
    # --------------------------------------------------------

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

        value_input_option=
            "USER_ENTERED"

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


# ============================================================
# FINAL SUMMARY
# ============================================================


print()

print("=" * 70)

print(
    "JOB HUNTER COMPLETED"
)

print("=" * 70)

print()

print(
    f"Total processed: "
    f"{len(jobs)}"
)

print(
    f"New jobs added: "
    f"{len(new_rows)}"
)

print()

print(
    "Sources:"
)

print(
    "  ✓ LinkedIn / Indeed / Google"
)

print(
    "  ✓ Public Facebook discovery"
)

print()

print(
    "Facebook search window: "
    "approximately last 30 days"
)

print()

print("=" * 70)
