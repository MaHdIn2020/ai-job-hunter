import os
import json
import hashlib
import re
from datetime import datetime, timezone

import requests
import gspread
import pandas as pd

from google.oauth2.service_account import Credentials
from jobspy import scrape_jobs


# ============================================================
# CONFIGURATION
# ============================================================

LOCATION = "Dhaka, Bangladesh"

RESULTS_PER_SEARCH = 15

# Job-board results: last 7 days
JOB_BOARD_HOURS_OLD = 168

# Facebook jobs: keep for 30 days
FACEBOOK_RETENTION_DAYS = 30

# ------------------------------------------------------------
# IMPORTANT
#
# Set this to True for ONE run only.
#
# It will completely clear the current Google Sheet
# and create a fresh set of results.
#
# AFTER THE FIRST SUCCESSFUL RUN:
#
#     WIPE_SHEET_ON_START = False
#
# Otherwise your Sheet will be erased every 6 hours.
# ------------------------------------------------------------

WIPE_SHEET_ON_START = False


# ============================================================
# GOOGLE SHEETS
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets"
]


credentials = Credentials.from_service_account_info(
    json.loads(
        os.environ["GOOGLE_CREDENTIALS_JSON"]
    ),
    scopes=SCOPES
)


client = gspread.authorize(
    credentials
)


spreadsheet = client.open_by_key(
    os.environ["GOOGLE_SHEET_ID"]
)


worksheet = spreadsheet.sheet1


# ============================================================
# GOOGLE SHEET COLUMNS
# ============================================================

HEADERS = [

    "Job ID",

    "Job Title",

    "Company",

    "Location",

    "Date Posted",

    "Job URL",

    "Source",

    "Job Type",

    "Date Found",

    "Status",

    "Fresher Friendly",

    "AI/ML Relevance",

    "Search Query",

    "Location Verification",

    "Facebook Confidence",

    "Snippet",

]


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def clean_text(value):

    if value is None:
        return ""

    try:

        if pd.isna(value):
            return ""

    except Exception:
        pass

    return str(value).strip()


# ------------------------------------------------------------
# Normalize text
# ------------------------------------------------------------


def normalize_text(text):

    text = clean_text(text)

    text = text.lower()

    text = text.replace(
        "\n",
        " "
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ------------------------------------------------------------
# Count keywords
# ------------------------------------------------------------


def count_keywords(
    text,
    keywords
):

    text = normalize_text(text)

    return sum(

        1

        for keyword in keywords

        if keyword in text

    )


# ============================================================
# KEYWORDS
# ============================================================


# ------------------------------------------------------------
# AI / ML keywords
# ------------------------------------------------------------

AI_ML_KEYWORDS = [

    "artificial intelligence",

    "artificial-intelligence",

    "ai engineer",

    "ai developer",

    "ai intern",

    "ai internship",

    "ai trainee",

    "ai research",

    "machine learning",

    "machine-learning",

    "ml engineer",

    "ml developer",

    "ml intern",

    "ml internship",

    "ml trainee",

    "ml research",

    "deep learning",

    "deep-learning",

    "deep learning engineer",

    "computer vision",

    "computer-vision",

    "computer vision engineer",

    "computer vision intern",

    "natural language processing",

    "natural-language processing",

    "nlp",

    "nlp engineer",

    "nlp intern",

    "generative ai",

    "generative-ai",

    "genai",

    "large language model",

    "large language models",

    "llm",

]


# ------------------------------------------------------------
# Fresher-friendly keywords
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# Job keywords
# ------------------------------------------------------------

JOB_KEYWORDS = [

    "hiring",

    "we are hiring",

    "we're hiring",

    "job",

    "jobs",

    "job opening",

    "job openings",

    "vacancy",

    "vacancies",

    "position",

    "open position",

    "career opportunity",

    "career opportunities",

    "apply",

    "apply now",

    "application",

    "recruitment",

    "recruiting",

    "recruit",

    "send your cv",

    "send cv",

    "submit your cv",

    "resume",

    "cv",

    "join our team",

    "join the team",

    "looking for",

    "seeking",

]


# ------------------------------------------------------------
# Noise keywords
# ------------------------------------------------------------

NOISE_KEYWORDS = [

    "course",

    "courses",

    "training",

    "training program",

    "workshop",

    "webinar",

    "seminar",

    "bootcamp",

    "certificate",

    "certification",

    "learn ai",

    "learn machine learning",

    "tutorial",

    "roadmap",

    "conference",

    "event",

    "meetup",

    "hackathon",

    "competition",

    "contest",

    "free class",

    "free course",

]


# ------------------------------------------------------------
# Senior keywords
# ------------------------------------------------------------

SENIOR_KEYWORDS = [

    "senior",

    "sr.",

    "sr ",

    "lead",

    "principal",

    "staff engineer",

    "engineering manager",

    "product manager",

    "manager",

    "management",

    "director",

    "head of",

    "architect",

    "vice president",

    "vp ",

]


# ------------------------------------------------------------
# Bangladesh keywords
# ------------------------------------------------------------

BANGLADESH_KEYWORDS = [

    "bangladesh",

    "bangladeshi",

    "dhaka",

    "chattogram",

    "chittagong",

    "sylhet",

    "rajshahi",

    "khulna",

    "barisal",

    "rangpur",

    "mymensingh",

    "gazipur",

    "narayanganj",

    "cumilla",

    "comilla",

    "bogura",

    "bdt",

    "৳",

    "+880",

    "bangladesh time",

    "bst",

    "bd time",

]


# ------------------------------------------------------------
# Foreign location keywords
# ------------------------------------------------------------

FOREIGN_LOCATIONS = [

    "united states",

    "united states of america",

    "usa",

    "u.s.",

    "us only",

    "us based",

    "canada",

    "canada only",

    "uk",

    "united kingdom",

    "uk only",

    "australia",

    "australia only",

    "new zealand",

    "germany",

    "france",

    "netherlands",

    "sweden",

    "denmark",

    "norway",

    "finland",

    "ireland",

    "singapore",

    "dubai",

    "uae",

    "united arab emirates",

    "india",

    "india only",

    "pakistan",

    "europe",

    "european union",

]


# ============================================================
# STAGE 1 SEARCH TERMS
# ============================================================


SEARCH_TERMS = [

    "machine learning engineer",

    "machine learning intern",

    "machine learning trainee",

    "machine learning developer",

    "machine learning research intern",

    "machine learning research assistant",

    "AI engineer",

    "AI intern",

    "AI trainee",

    "AI developer",

    "artificial intelligence engineer",

    "artificial intelligence intern",

    "artificial intelligence trainee",

    "junior AI engineer",

    "junior machine learning engineer",

    "entry level AI engineer",

    "entry level machine learning",

    "graduate AI engineer",

    "graduate machine learning engineer",

    "AI engineer fresher",

    "ML engineer fresher",

    "AI research intern",

    "AI research assistant",

    "deep learning engineer",

    "deep learning intern",

    "computer vision engineer",

    "computer vision intern",

    "NLP engineer",

    "NLP intern",

    "natural language processing intern",

]


SITES = [

    "linkedin",

    "indeed",

    "google",

]


# ============================================================
# FACEBOOK SEARCH QUERIES
# ============================================================


FACEBOOK_QUERIES = [

    # AI Engineer
    'site:facebook.com "AI Engineer" Bangladesh hiring',

    'site:facebook.com "AI Engineer" Dhaka hiring',

    'site:facebook.com "Artificial Intelligence Engineer" Bangladesh',

    # Machine Learning
    'site:facebook.com "Machine Learning Engineer" Bangladesh',

    'site:facebook.com "Machine Learning Engineer" Dhaka',

    # Internships
    'site:facebook.com "AI Intern" Bangladesh',

    'site:facebook.com "AI Intern" Dhaka',

    'site:facebook.com "Machine Learning Intern" Bangladesh',

    'site:facebook.com "Machine Learning Intern" Dhaka',

    # Trainee
    'site:facebook.com "AI Trainee" Bangladesh',

    'site:facebook.com "AI Trainee" Dhaka',

    'site:facebook.com "Machine Learning Trainee" Bangladesh',

    # Junior / fresher
    'site:facebook.com "Junior AI Engineer" Bangladesh',

    'site:facebook.com "Junior AI Engineer" Dhaka',

    'site:facebook.com "Junior Machine Learning" Bangladesh',

    # Research
    'site:facebook.com "AI Research Intern" Bangladesh',

    'site:facebook.com "Machine Learning Research Intern" Bangladesh',

    # Facebook groups
    'site:facebook.com/groups "AI jobs" Bangladesh',

    'site:facebook.com/groups "AI internship" Bangladesh',

    'site:facebook.com/groups "machine learning jobs" Bangladesh',

]


# ============================================================
# GOOGLE SHEET SETUP
# ============================================================


def setup_sheet():

    """
    Create/reset the header row.
    """

    if WIPE_SHEET_ON_START:

        print()
        print(
            "WARNING: WIPING EXISTING GOOGLE SHEET..."
        )

        worksheet.clear()

        worksheet.update(
            "A1",
            [HEADERS]
        )

        print(
            "Existing jobs removed."
        )

    else:

        existing_headers = (
            worksheet.row_values(1)
        )

        if existing_headers != HEADERS:

            worksheet.update(
                "A1",
                [HEADERS]
            )


# ============================================================
# DELETE OLD FACEBOOK JOBS
# ============================================================


def remove_old_facebook_jobs(
    days=30
):

    """
    Remove Facebook jobs older than
    `days`.

    Job-board jobs are preserved.
    """

    if WIPE_SHEET_ON_START:

        return


    print()
    print(
        f"Checking Facebook jobs older "
        f"than {days} days..."
    )


    rows = worksheet.get_all_values()


    if len(rows) <= 1:

        return


    headers = rows[0]


    try:

        source_index = headers.index(
            "Source"
        )

        date_posted_index = headers.index(
            "Date Posted"
        )

        date_found_index = headers.index(
            "Date Found"
        )

    except ValueError:

        print(
            "Required columns not found."
        )

        return


    now = datetime.now(
        timezone.utc
    )


    rows_to_delete = []


    for row_number, row in enumerate(

        rows[1:],

        start=2

    ):


        if len(row) <= source_index:

            continue


        source = normalize_text(

            row[source_index]

        )


        # Only Facebook jobs
        if source != "facebook":

            continue


        date_posted = ""

        if len(row) > date_posted_index:

            date_posted = clean_text(

                row[date_posted_index]

            )


        date_found = ""

        if len(row) > date_found_index:

            date_found = clean_text(

                row[date_found_index]

            )


        job_date = None


        formats = [

            "%Y-%m-%d",

            "%Y-%m-%d %H:%M",

            "%Y-%m-%d %H:%M UTC",

            "%Y-%m-%dT%H:%M:%S",

            "%Y-%m-%dT%H:%M:%S.%f",

        ]


        # Try Date Posted
        if date_posted:

            for fmt in formats:

                try:

                    parsed = datetime.strptime(
                        date_posted,
                        fmt
                    )

                    job_date = parsed.replace(
                        tzinfo=timezone.utc
                    )

                    break

                except ValueError:

                    continue


        # Fall back to Date Found
        if job_date is None and date_found:

            for fmt in formats:

                try:

                    parsed = datetime.strptime(
                        date_found,
                        fmt
                    )

                    job_date = parsed.replace(
                        tzinfo=timezone.utc
                    )

                    break

                except ValueError:

                    continue


        if job_date is None:

            continue


        age_days = (

            now - job_date

        ).total_seconds() / 86400


        if age_days > days:

            rows_to_delete.append(
                row_number
            )


    # Delete from bottom upward
    for row_number in reversed(
        rows_to_delete
    ):

        worksheet.delete_rows(
            row_number
        )


    print(
        f"Removed {len(rows_to_delete)} "
        f"expired Facebook jobs."
    )


# ============================================================
# JOB ID
# ============================================================


def create_job_id(row):

    job_url = clean_text(
        row.get("job_url")
    )


    if job_url:

        unique_string = (
            job_url.lower().strip()
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


# ============================================================
# AI/ML TITLE FILTER
# ============================================================


def is_relevant_title(
    title
):

    title = normalize_text(
        title
    )


    if not title:

        return False


    has_ai_ml = any(

        keyword in title

        for keyword in AI_ML_KEYWORDS

    )


    if not has_ai_ml:

        return False


    has_senior = any(

        keyword in title

        for keyword in SENIOR_KEYWORDS

    )


    if has_senior:

        return False


    return True


# ============================================================
# FRESHER CLASSIFICATION
# ============================================================


def classify_fresher(
    text
):

    text = normalize_text(
        text
    )


    if any(

        keyword in text

        for keyword in FRESHER_KEYWORDS

    ):

        return "YES"


    return "MAYBE"


# ============================================================
# AI/ML RELEVANCE SCORE
# ============================================================


def relevance_score(
    text
):

    text = normalize_text(
        text
    )


    score = 0


    if "machine learning" in text:
        score += 40


    if "artificial intelligence" in text:
        score += 40


    if "ai engineer" in text:
        score += 40


    if "ml engineer" in text:
        score += 40


    if "deep learning" in text:
        score += 30


    if "computer vision" in text:
        score += 30


    if "natural language processing" in text:
        score += 30


    if "nlp" in text:
        score += 20


    if "generative ai" in text:
        score += 30


    if "llm" in text:
        score += 25


    if any(

        keyword in text

        for keyword in FRESHER_KEYWORDS

    ):

        score += 20


    return min(
        score,
        100
    )


# ============================================================
# FACEBOOK LOCATION ANALYSIS
# ============================================================


def analyze_location(
    text
):

    text = normalize_text(
        text
    )


    bd_matches = [

        keyword

        for keyword in BANGLADESH_KEYWORDS

        if keyword in text

    ]


    foreign_matches = [

        keyword

        for keyword in FOREIGN_LOCATIONS

        if keyword in text

    ]


    # Bangladesh explicitly mentioned
    if bd_matches:

        return {

            "status":
                "BANGLADESH",

            "score":
                40,

            "matches":
                bd_matches,

        }


    # Foreign-only
    if foreign_matches:

        return {

            "status":
                "FOREIGN",

            "score":
                -50,

            "matches":
                foreign_matches,

        }


    return {

        "status":
            "UNKNOWN",

        "score":
            0,

        "matches":
            [],

    }


# ============================================================
# REMOTE ANALYSIS
# ============================================================


def is_remote(
    text
):

    text = normalize_text(
        text
    )


    remote_keywords = [

        "remote",

        "work from home",

        "wfh",

        "fully remote",

        "remote position",

        "remote role",

        "remote job",

    ]


    return any(

        keyword in text

        for keyword in remote_keywords

    )


# ============================================================
# FACEBOOK RESULT SCORING
# ============================================================


def analyze_facebook_result(
    title,
    snippet
):

    combined = (

        clean_text(title)
        + " "
        + clean_text(snippet)

    )


    text = normalize_text(
        combined
    )


    # --------------------------------------------------------
    # AI/ML check
    # --------------------------------------------------------

    ai_count = count_keywords(

        text,

        AI_ML_KEYWORDS

    )


    if ai_count == 0:

        return {

            "accepted": False,

            "score": 0,

            "reason":
                "Not AI/ML related",

            "location":
                "UNKNOWN",

        }


    # --------------------------------------------------------
    # Job check
    # --------------------------------------------------------

    job_count = count_keywords(

        text,

        JOB_KEYWORDS

    )


    if job_count == 0:

        return {

            "accepted": False,

            "score": 0,

            "reason":
                "No clear hiring/job signal",

            "location":
                "UNKNOWN",

        }


    # --------------------------------------------------------
    # Noise check
    # --------------------------------------------------------

    noise_count = count_keywords(

        text,

        NOISE_KEYWORDS

    )


    if noise_count >= 2:

        return {

            "accepted": False,

            "score": 0,

            "reason":
                "Likely course/event/training",

            "location":
                "UNKNOWN",

        }


    # --------------------------------------------------------
    # Senior role check
    # --------------------------------------------------------

    senior_count = count_keywords(

        text,

        SENIOR_KEYWORDS

    )


    if senior_count > 0:

        return {

            "accepted": False,

            "score": 0,

            "reason":
                "Senior/management role",

            "location":
                "UNKNOWN",

        }


    # --------------------------------------------------------
    # Location
    # --------------------------------------------------------

    location = analyze_location(
        text
    )


    # Foreign-only result
    if location[
        "status"
    ] == "FOREIGN":

        return {

            "accepted": False,

            "score": 0,

            "reason":
                "Foreign-only location",

            "location":
                "FOREIGN",

        }


    # --------------------------------------------------------
    # Score
    # --------------------------------------------------------

    score = 0


    # AI/ML
    score += min(

        ai_count * 15,

        45

    )


    # Job signal
    score += min(

        job_count * 10,

        30

    )


    # Bangladesh
    score += location[
        "score"
    ]


    # Fresher
    fresher_count = count_keywords(

        text,

        FRESHER_KEYWORDS

    )


    score += min(

        fresher_count * 10,

        20

    )


    # Remote
    remote = is_remote(
        text
    )


    # --------------------------------------------------------
    # Remote jobs require Bangladesh evidence
    # --------------------------------------------------------

    if remote:

        if location[
            "status"
        ] != "BANGLADESH":

            return {

                "accepted": False,

                "score": score,

                "reason":
                    "Remote but Bangladesh "
                    "eligibility unclear",

                "location":
                    "UNKNOWN",

            }


    # --------------------------------------------------------
    # Final decision
    # --------------------------------------------------------

    if location[
        "status"
    ] == "BANGLADESH":

        if score >= 40:

            return {

                "accepted": True,

                "score": min(
                    score,
                    100
                ),

                "reason":
                    "Strong Bangladesh "
                    "AI/ML job signal",

                "location":
                    "BANGLADESH",

            }


    return {

        "accepted": False,

        "score": score,

        "reason":
            "Bangladesh eligibility "
            "not sufficiently confirmed",

        "location":
            "UNKNOWN",

    }


# ============================================================
# SERPER FACEBOOK SEARCH
# ============================================================


def search_facebook(
    query
):

    api_key = os.environ.get(
        "SERPER_API_KEY"
    )


    if not api_key:

        print(
            "ERROR: SERPER_API_KEY missing."
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

        "q":
            query,

        "gl":
            "bd",

        "hl":
            "en",

        "num":
            10,

        # Last month
        "tbs":
            "qdr:m",

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
            f"Serper error: {e}"
        )

        return []


# ============================================================
# STAGE 1: JOB BOARDS
# ============================================================


def collect_job_board_jobs():

    print()
    print("=" * 70)
    print("STAGE 1: JOB BOARDS")
    print("=" * 70)


    all_jobs = []


    for index, search_term in enumerate(

        SEARCH_TERMS,

        start=1

    ):


        print()

        print(

            f"[{index}/"
            f"{len(SEARCH_TERMS)}] "
            f"{search_term}"

        )


        try:

            jobs = scrape_jobs(

                site_name=SITES,

                search_term=search_term,

                location=LOCATION,

                results_wanted=
                    RESULTS_PER_SEARCH,

                hours_old=
                    JOB_BOARD_HOURS_OLD,

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


    return all_jobs


# ============================================================
# STAGE 2: FACEBOOK
# ============================================================


def collect_facebook_jobs():

    print()
    print("=" * 70)
    print("STAGE 2: FACEBOOK")
    print("=" * 70)


    facebook_jobs = []

    seen_urls = set()


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
            query
        )


        results = search_facebook(
            query
        )


        print(

            f"    Results: "
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


            # Must be Facebook
            if (
                "facebook.com"
                not in link.lower()
            ):

                continue


            normalized_url = (
                link.lower().strip()
            )


            if normalized_url in seen_urls:

                continue


            seen_urls.add(
                normalized_url
            )


            analysis = (
                analyze_facebook_result(
                    title,
                    snippet
                )
            )


            if not analysis[
                "accepted"
            ]:

                print()

                print(
                    f"    SKIPPED: {title}"
                )

                print(

                    f"       "
                    f"{analysis['reason']}"

                )

                continue


            print()

            print(
                f"    ACCEPTED: {title}"
            )

            print(

                f"       "
                f"Confidence: "
                f"{analysis['score']}"

            )


            combined_text = (

                title
                + " "
                + snippet

            )


            facebook_job = {

                "title":
                    title,

                "company":
                    "",

                "location":
                    "Bangladesh",

                "date_posted":
                    "",

                "job_url":
                    link,

                "site":
                    "Facebook",

                "job_type":
                    "Remote"
                    if is_remote(
                        combined_text
                    )
                    else "",

                "search_term":
                    query,

                "snippet":
                    snippet,

                "source_type":
                    "Facebook",

                "fresher_friendly":
                    classify_fresher(
                        combined_text
                    ),

                "ai_ml_relevance":
                    relevance_score(
                        combined_text
                    ),

                "facebook_confidence":
                    analysis[
                        "score"
                    ],

                "location_verification":
                    analysis[
                        "location"
                    ],

            }


            facebook_jobs.append(
                facebook_job
            )


    print()

    print(

        f"Accepted Facebook jobs: "
        f"{len(facebook_jobs)}"

    )


    if facebook_jobs:

        facebook_df = pd.DataFrame(
            facebook_jobs
        )

        return [
            facebook_df
        ]


    return []


# ============================================================
# PREPARE JOB DATA
# ============================================================


def prepare_jobs(
    job_dataframes
):

    if not job_dataframes:

        return pd.DataFrame()


    jobs = pd.concat(

        job_dataframes,

        ignore_index=True

    )


    print()

    print(
        f"Total raw jobs: "
        f"{len(jobs)}"
    )


    # --------------------------------------------------------
    # Job ID
    # --------------------------------------------------------

    jobs[
        "job_id"
    ] = jobs.apply(

        create_job_id,

        axis=1

    )


    # --------------------------------------------------------
    # Remove duplicate Job IDs
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # AI/ML filter
    # --------------------------------------------------------

    before = len(jobs)


    jobs = jobs[

        jobs[
            "title"
        ].apply(
            is_relevant_title
        )

    ].copy()


    print(

        f"Non-AI/ML jobs removed: "
        f"{before - len(jobs)}"

    )


    # --------------------------------------------------------
    # Ensure optional columns
    # --------------------------------------------------------

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


    if (
        "facebook_confidence"
        not in jobs.columns
    ):

        jobs[
            "facebook_confidence"
        ] = ""


    if (
        "location_verification"
        not in jobs.columns
    ):

        jobs[
            "location_verification"
        ] = ""


    if (
        "snippet"
        not in jobs.columns
    ):

        jobs[
            "snippet"
        ] = ""


    # --------------------------------------------------------
    # Classification
    # --------------------------------------------------------

    jobs[
        "fresher_friendly"
    ] = jobs.apply(

        lambda row:

        clean_text(

            row[
                "fresher_friendly"
            ]

        )

        or classify_fresher(

            clean_text(
                row.get("title")
            )
            + " "
            + clean_text(
                row.get("snippet")
            )

        ),

        axis=1

    )


    jobs[
        "ai_ml_relevance"
    ] = jobs.apply(

        lambda row:

        clean_text(

            row[
                "ai_ml_relevance"
            ]

        )

        or relevance_score(

            clean_text(
                row.get("title")
            )
            + " "
            + clean_text(
                row.get("snippet")
            )

        ),

        axis=1

    )


    return jobs


# ============================================================
# GET EXISTING JOB IDS
# ============================================================


def get_existing_ids():

    rows = worksheet.get_all_values()


    if len(rows) <= 1:

        return set()


    existing_ids = set()


    for row in rows[1:]:

        if row:

            existing_ids.add(
                clean_text(
                    row[0]
                )
            )


    return existing_ids


# ============================================================
# ADD JOBS TO GOOGLE SHEETS
# ============================================================


def upload_jobs(
    jobs
):

    if jobs.empty:

        print()
        print(
            "No jobs to upload."
        )

        return 0


    existing_ids = (
        get_existing_ids()
    )


    print()

    print(

        f"Existing Sheet jobs: "
        f"{len(existing_ids)}"

    )


    new_rows = []

    seen_ids = set()


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


        if not job_id:

            continue


        # Existing job
        if job_id in existing_ids:

            continue


        # Duplicate current run
        if job_id in seen_ids:

            continue


        seen_ids.add(
            job_id
        )


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
            job.get(
                "fresher_friendly"
            )
        )


        relevance = clean_text(
            job.get(
                "ai_ml_relevance"
            )
        )


        search_query = clean_text(
            job.get(
                "search_term"
            )
        )


        location_verification = (
            clean_text(
                job.get(
                    "location_verification"
                )
            )
        )


        facebook_confidence = (
            clean_text(
                job.get(
                    "facebook_confidence"
                )
            )
        )


        snippet = clean_text(
            job.get(
                "snippet"
            )
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

            search_query,

            location_verification,

            facebook_confidence,

            snippet,

        ])


    if not new_rows:

        print()

        print(
            "No NEW jobs to add."
        )

        return 0


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


    return len(new_rows)


# ============================================================
# MAIN
# ============================================================


def main():

    print()

    print("=" * 70)

    print(
        "AI JOB HUNTER"
    )

    print("=" * 70)


    # --------------------------------------------------------
    # Sheet setup / one-time wipe
    # --------------------------------------------------------

    setup_sheet()


    # --------------------------------------------------------
    # Remove old Facebook posts
    # --------------------------------------------------------

    remove_old_facebook_jobs(
        FACEBOOK_RETENTION_DAYS
    )


    # --------------------------------------------------------
    # Stage 1
    # --------------------------------------------------------

    job_board_data = (
        collect_job_board_jobs()
    )


    # --------------------------------------------------------
    # Stage 2
    # --------------------------------------------------------

    facebook_data = (
        collect_facebook_jobs()
    )


    # --------------------------------------------------------
    # Combine
    # --------------------------------------------------------

    all_data = (
        job_board_data
        + facebook_data
    )


    # --------------------------------------------------------
    # Prepare
    # --------------------------------------------------------

    jobs = prepare_jobs(
        all_data
    )


    # --------------------------------------------------------
    # Upload
    # --------------------------------------------------------

    new_count = upload_jobs(
        jobs
    )


    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()

    print("=" * 70)

    print(
        "JOB HUNTER COMPLETED"
    )

    print("=" * 70)

    print()

    print(
        f"Processed jobs: "
        f"{len(jobs)}"
    )

    print(
        f"New jobs added: "
        f"{new_count}"
    )

    print()

    print(
        "Job sources:"
    )

    print(
        "  ✓ LinkedIn"
    )

    print(
        "  ✓ Indeed"
    )

    print(
        "  ✓ Google Jobs"
    )

    print(
        "  ✓ Facebook public search"
    )

    print()

    print(
        "Facebook filtering:"
    )

    print(
        "  ✓ AI/ML relevance"
    )

    print(
        "  ✓ Job/hiring signal"
    )

    print(
        "  ✓ Bangladesh verification"
    )

    print(
        "  ✓ Foreign-location rejection"
    )

    print(
        "  ✓ Senior-role rejection"
    )

    print(
        "  ✓ Course/event rejection"
    )

    print(
        "  ✓ Remote-location verification"
    )

    print(
        "  ✓ Fresher/intern detection"
    )

    print()

    print("=" * 70)


if __name__ == "__main__":

    main()
