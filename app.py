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

# Job-board searches only look for jobs from the last 7 days
JOB_BOARD_HOURS_OLD = 168

# Facebook jobs/posts older than this are removed
FACEBOOK_RETENTION_DAYS = 30


# ============================================================
# IMPORTANT
# ============================================================
#
# TRUE:
#   Completely clears the Google Sheet before the first run.
#
# FALSE:
#   Keeps existing jobs and only adds new jobs.
#
# Set TRUE for ONE run after installing this version.
# Then change it to FALSE.
#
# ============================================================

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


client = gspread.authorize(credentials)


spreadsheet = client.open_by_key(
    os.environ["GOOGLE_SHEET_ID"]
)


worksheet = spreadsheet.sheet1


# ============================================================
# GOOGLE SHEET HEADERS
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

    "Post Classification",

    "Snippet",

]


# ============================================================
# TEXT HELPERS
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


def normalize_text(text):

    text = clean_text(text)

    text = text.lower()

    text = text.replace("\n", " ")

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def count_keywords(text, keywords):

    text = normalize_text(text)

    return sum(
        1
        for keyword in keywords
        if keyword in text
    )


# ============================================================
# AI / ML KEYWORDS
# ============================================================

AI_ML_KEYWORDS = [

    "artificial intelligence",

    "artificial-intelligence",

    "ai engineer",

    "ai developer",

    "ai intern",

    "ai internship",

    "ai trainee",

    "ai research",

    "ai researcher",

    "ai scientist",

    "machine learning",

    "machine-learning",

    "machine learning engineer",

    "machine learning intern",

    "machine learning internship",

    "machine learning trainee",

    "machine learning developer",

    "machine learning researcher",

    "machine learning scientist",

    "ml engineer",

    "ml developer",

    "ml intern",

    "ml internship",

    "ml trainee",

    "ml researcher",

    "deep learning",

    "deep-learning",

    "deep learning engineer",

    "deep learning intern",

    "computer vision",

    "computer-vision",

    "computer vision engineer",

    "computer vision intern",

    "natural language processing",

    "natural-language processing",

    "nlp engineer",

    "nlp intern",

    "nlp developer",

    "generative ai",

    "generative-ai",

    "genai",

    "gen ai",

    "large language model",

    "large language models",

    "llm",

    "llm engineer",

    "llm intern",

    "llm developer",

]


# ============================================================
# OPTIONAL RELATED ROLES
# ============================================================

RELATED_AI_ROLES = [

    "data scientist",

    "data science intern",

    "data science trainee",

    "research assistant",

    "ai research assistant",

    "machine learning research assistant",

]


# ============================================================
# FRESHER / ENTRY LEVEL KEYWORDS
# ============================================================

FRESHER_KEYWORDS = [

    "intern",

    "internship",

    "trainee",

    "junior",

    "entry level",

    "entry-level",

    "graduate",

    "fresh graduate",

    "fresher",

    "new grad",

    "new graduate",

    "entry-level",

    "research intern",

    "research assistant",

]


# ============================================================
# EMPLOYER / HIRING SIGNALS
# ============================================================

HIRING_KEYWORDS = [

    "we are hiring",

    "we're hiring",

    "we are looking for",

    "we're looking for",

    "our team is hiring",

    "our team is looking for",

    "hiring",

    "job opening",

    "job openings",

    "vacancy",

    "vacancies",

    "open position",

    "open positions",

    "position available",

    "positions available",

    "career opportunity",

    "career opportunities",

    "join our team",

    "join the team",

    "join us",

    "recruiting",

    "recruitment",

    "recruit",

    "apply now",

    "apply here",

    "send your cv",

    "send cv",

    "submit your cv",

    "submit cv",

    "send resume",

    "submit resume",

    "applications are open",

    "applications open",

    "candidates can apply",

    "candidates are invited",

    "looking for candidates",

    "seeking candidates",

    "we need",

    "we need a",

    "we need an",

    "hiring for",

    "hiring an",

    "hiring a",

]


# ============================================================
# APPLICANT / JOB-SEEKER SIGNALS
# ============================================================
#
# These are extremely important.
#
# We DON'T want:
#
# "I am seeking a job"
# "Looking for an AI job"
# "I am looking for opportunities"
#
# Those are people searching for jobs, not employers.
#
# ============================================================

APPLICANT_KEYWORDS = [

    "i am looking for a job",

    "i'm looking for a job",

    "i am looking for jobs",

    "i'm looking for jobs",

    "i am seeking a job",

    "i'm seeking a job",

    "i am seeking jobs",

    "i'm seeking jobs",

    "looking for a job",

    "looking for jobs",

    "seeking a job",

    "seeking jobs",

    "seeking employment",

    "looking for employment",

    "looking for work",

    "seeking work",

    "need a job",

    "need a job urgently",

    "need employment",

    "job seeker",

    "jobseeker",

    "actively looking for a job",

    "actively seeking a job",

    "open to work",

    "open for work",

    "available for work",

    "available for opportunities",

    "looking for opportunities",

    "seeking opportunities",

    "looking for an opportunity",

    "seeking an opportunity",

    "please help me find a job",

    "help me find a job",

    "can anyone help me find a job",

    "any job leads",

    "job leads",

]


# ============================================================
# NOISE / NON-JOB KEYWORDS
# ============================================================

NOISE_KEYWORDS = [

    "course",

    "courses",

    "training",

    "training program",

    "training programme",

    "workshop",

    "webinar",

    "seminar",

    "bootcamp",

    "certificate",

    "certification",

    "learn ai",

    "learn machine learning",

    "learn artificial intelligence",

    "tutorial",

    "roadmap",

    "conference",

    "event",

    "events",

    "meetup",

    "hackathon",

    "competition",

    "contest",

    "free class",

    "free course",

    "cohort",

    "enrollment",

    "enrolment",

    "scholarship",

]


# ============================================================
# SENIOR / EXPERIENCED ROLES
# ============================================================

SENIOR_KEYWORDS = [

    "senior",

    "sr.",

    "sr ",

    "lead",

    "principal",

    "staff engineer",

    "staff machine learning",

    "staff ai",

    "engineering manager",

    "product manager",

    "manager",

    "management",

    "director",

    "head of",

    "architect",

    "vice president",

    "vp ",

    "chief",

]


# ============================================================
# BANGLADESH LOCATION KEYWORDS
# ============================================================

BANGLADESH_LOCATIONS = [

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

    "cox's bazar",

    "cox bazar",

    "savar",

    "uttara",

    "mirpur",

    "banani",

    "gulshan",

    "motijheel",

    "dhanmondi",

    "bdt",

    "৳",

    "+880",

]


# ============================================================
# FOREIGN LOCATION KEYWORDS
# ============================================================

FOREIGN_LOCATIONS = [

    # USA
    "united states",

    "united states of america",

    "usa",

    "u.s.a",

    "u.s.",

    "us only",

    "us-based",

    "us based",

    "new york",

    "california",

    "texas",

    "florida",

    "washington dc",

    "san francisco",

    "los angeles",

    "chicago",

    "seattle",

    "boston",

    "new jersey",

    # Canada
    "canada",

    "canada only",

    "toronto",

    "vancouver",

    "ontario",

    "montreal",

    # UK
    "united kingdom",

    "uk only",

    "london",

    "england",

    "scotland",

    "manchester",

    # India
    "india",

    "india only",

    "pune",

    "mumbai",

    "bangalore",

    "bengaluru",

    "hyderabad",

    "delhi",

    "new delhi",

    "gurgaon",

    "gurugram",

    "noida",

    "chennai",

    "kolkata",

    # Sri Lanka
    "sri lanka",

    "colombo",

    "kandy",

    # Australia
    "australia",

    "sydney",

    "melbourne",

    "brisbane",

    "perth",

    # New Zealand
    "new zealand",

    "auckland",

    # Europe
    "germany",

    "berlin",

    "france",

    "paris",

    "netherlands",

    "amsterdam",

    "sweden",

    "stockholm",

    "denmark",

    "copenhagen",

    "norway",

    "oslo",

    "finland",

    "helsinki",

    "ireland",

    "dublin",

    # Middle East
    "dubai",

    "uae",

    "united arab emirates",

    "abu dhabi",

    "qatar",

    "doha",

    "saudi arabia",

    "riyadh",

    # Asia
    "singapore",

    "pakistan",

    "karachi",

    "lahore",

    "islamabad",

]


# ============================================================
# REMOTE KEYWORDS
# ============================================================

REMOTE_KEYWORDS = [

    "remote",

    "fully remote",

    "remote position",

    "remote role",

    "remote job",

    "work from home",

    "wfh",

    "home based",

    "work-from-home",

]


# ============================================================
# NEGATIVE REMOTE / FOREIGN RESTRICTIONS
# ============================================================

FOREIGN_REMOTE_RESTRICTIONS = [

    "us only",

    "usa only",

    "united states only",

    "us-based only",

    "us based only",

    "canada only",

    "uk only",

    "india only",

    "australia only",

    "europe only",

    "eu only",

    "must be located in the us",

    "must be based in the us",

    "must be located in usa",

    "must be based in usa",

    "must be located in india",

    "must be based in india",

    "must be located in canada",

    "must be based in canada",

    "must be located in uk",

    "must be based in uk",

]


# ============================================================
# SHEET SETUP
# ============================================================

def setup_sheet():

    if WIPE_SHEET_ON_START:

        print()
        print("=" * 70)
        print("CLEARING EXISTING GOOGLE SHEET")
        print("=" * 70)

        worksheet.clear()

        worksheet.update(
            "A1",
            [HEADERS]
        )

        print("Existing jobs deleted.")

    else:

        existing_headers = worksheet.row_values(1)

        if existing_headers != HEADERS:

            worksheet.update(
                "A1",
                [HEADERS]
            )


# ============================================================
# JOB ID
# ============================================================

def create_job_id(row):

    url = clean_text(
        row.get("job_url")
    )

    if url:

        unique_value = url.lower().strip()

    else:

        unique_value = "|".join([

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
        unique_value.encode("utf-8")
    ).hexdigest()[:16]


# ============================================================
# AI/ML TITLE FILTER
# ============================================================

def is_ai_ml_title(title):

    title = normalize_text(title)

    if not title:
        return False

    ai_terms = [

        "ai engineer",
        "ai developer",
        "ai intern",
        "ai trainee",
        "ai researcher",
        "ai scientist",

        "machine learning",
        "ml engineer",
        "ml developer",
        "ml intern",
        "ml trainee",

        "deep learning",

        "computer vision",

        "nlp",

        "natural language processing",

        "generative ai",
        "genai",
        "gen ai",

        "llm",

        "artificial intelligence",

    ]

    return any(
        term in title
        for term in ai_terms
    )


# ============================================================
# FRESHER CLASSIFICATION
# ============================================================

def classify_fresher(text):

    text = normalize_text(text)

    if any(
        keyword in text
        for keyword in FRESHER_KEYWORDS
    ):
        return "YES"

    return "MAYBE"


# ============================================================
# AI/ML SCORE
# ============================================================

def relevance_score(text):

    text = normalize_text(text)

    score = 0

    strong_terms = [

        "machine learning",
        "machine-learning",
        "artificial intelligence",
        "ai engineer",
        "machine learning engineer",
        "ml engineer",

    ]

    medium_terms = [

        "deep learning",
        "computer vision",
        "natural language processing",
        "nlp",
        "generative ai",
        "genai",
        "llm",

    ]

    for term in strong_terms:

        if term in text:
            score += 20

    for term in medium_terms:

        if term in text:
            score += 10

    return min(
        score,
        100
    )


# ============================================================
# LOCATION ANALYSIS
# ============================================================

def analyze_location(text):

    text = normalize_text(text)

    bd_matches = [

        location

        for location in BANGLADESH_LOCATIONS

        if location in text

    ]

    foreign_matches = [

        location

        for location in FOREIGN_LOCATIONS

        if location in text

    ]

    return {
        "bangladesh": bd_matches,
        "foreign": foreign_matches
    }


# ============================================================
# CHECK REMOTE
# ============================================================

def contains_remote(text):

    text = normalize_text(text)

    return any(
        keyword in text
        for keyword in REMOTE_KEYWORDS
    )


# ============================================================
# CHECK FOREIGN REMOTE RESTRICTION
# ============================================================

def has_foreign_remote_restriction(text):

    text = normalize_text(text)

    return any(
        phrase in text
        for phrase in FOREIGN_REMOTE_RESTRICTIONS
    )


# ============================================================
# CHECK IF POST IS FROM JOB SEEKER
# ============================================================

def is_job_seeker_post(text):

    text = normalize_text(text)

    matches = [

        keyword

        for keyword in APPLICANT_KEYWORDS

        if keyword in text

    ]

    return matches


# ============================================================
# CHECK EMPLOYER SIGNAL
# ============================================================

def employer_hiring_signal(text):

    text = normalize_text(text)

    matches = [

        keyword

        for keyword in HIRING_KEYWORDS

        if keyword in text

    ]

    return matches


# ============================================================
# FACEBOOK CLASSIFIER
# ============================================================

def classify_facebook_post(
    title,
    snippet
):

    title_text = normalize_text(
        title
    )

    snippet_text = normalize_text(
        snippet
    )

    full_text = (

        title_text
        + " "
        + snippet_text

    )


    # ========================================================
    # STEP 1
    # IS THIS A JOB-SEEKER POST?
    # ========================================================

    applicant_matches = (
        is_job_seeker_post(
            full_text
        )
    )

    if applicant_matches:

        return {

            "accepted": False,

            "confidence": 0,

            "classification":
                "JOB SEEKER",

            "location":
                "REJECTED",

            "reason":
                "Post appears to be "
                "someone seeking employment",

        }


    # ========================================================
    # STEP 2
    # IS THIS A REAL JOB?
    # ========================================================

    hiring_matches = (
        employer_hiring_signal(
            full_text
        )
    )


    if not hiring_matches:

        return {

            "accepted": False,

            "confidence": 0,

            "classification":
                "NOT A JOB",

            "location":
                "REJECTED",

            "reason":
                "No employer hiring signal",

        }


    # ========================================================
    # STEP 3
    # IS IT AI/ML?
    # ========================================================

    ai_matches = [

        keyword

        for keyword in AI_ML_KEYWORDS

        if keyword in full_text

    ]


    related_matches = [

        keyword

        for keyword in RELATED_AI_ROLES

        if keyword in full_text

    ]


    if not ai_matches:

        if not related_matches:

            return {

                "accepted": False,

                "confidence": 0,

                "classification":
                    "NOT AI/ML",

                "location":
                    "REJECTED",

                "reason":
                    "No AI/ML role detected",

            }


    # ========================================================
    # STEP 4
    # REMOVE COURSES / TRAINING / EVENTS
    # ========================================================

    noise_matches = [

        keyword

        for keyword in NOISE_KEYWORDS

        if keyword in full_text

    ]


    if len(noise_matches) >= 2:

        return {

            "accepted": False,

            "confidence": 0,

            "classification":
                "NON-JOB",

            "location":
                "REJECTED",

            "reason":
                "Likely course/training/event",

        }


    # ========================================================
    # STEP 5
    # REJECT SENIOR ROLES
    # ========================================================

    senior_matches = [

        keyword

        for keyword in SENIOR_KEYWORDS

        if keyword in title_text

    ]


    if senior_matches:

        return {

            "accepted": False,

            "confidence": 0,

            "classification":
                "SENIOR ROLE",

            "location":
                "REJECTED",

            "reason":
                "Senior/management role",

        }


    # ========================================================
    # STEP 6
    # LOCATION
    # ========================================================

    location = analyze_location(
        full_text
    )

    bd_locations = location[
        "bangladesh"
    ]

    foreign_locations = location[
        "foreign"
    ]


    # ========================================================
    # HARD RULE:
    # FOREIGN CITY/COUNTRY IN JOB POST = REJECT
    #
    # This specifically catches:
    #
    # Pune
    # Colombo
    # USA
    # London
    # Toronto
    #
    # ========================================================

    if foreign_locations:

        # If foreign location exists AND there is no
        # explicit Bangladesh job-location evidence,
        # reject it.

        if not bd_locations:

            return {

                "accepted": False,

                "confidence": 0,

                "classification":
                    "FOREIGN JOB",

                "location":
                    "FOREIGN",

                "reason":
                    "Actual job appears "
                    "to be outside Bangladesh",

            }


        # Even if Bangladesh appears, we don't
        # automatically trust it.
        #
        # If a specific foreign city appears,
        # reject unless Bangladesh is explicitly
        # described as the job location.

        foreign_strong = [

            "pune",
            "mumbai",
            "bangalore",
            "bengaluru",
            "hyderabad",
            "delhi",
            "new delhi",
            "chennai",
            "colombo",
            "kandy",
            "new york",
            "california",
            "texas",
            "london",
            "toronto",
            "vancouver",
            "sydney",
            "melbourne",

        ]

        if any(
            city in full_text
            for city in foreign_strong
        ):

            return {

                "accepted": False,

                "confidence": 0,

                "classification":
                    "FOREIGN JOB",

                "location":
                    "FOREIGN",

                "reason":
                    "Foreign job location "
                    "detected",

            }


    # ========================================================
    # STEP 7
    # REMOTE JOBS
    # ========================================================

    remote = contains_remote(
        full_text
    )


    if remote:

        if has_foreign_remote_restriction(
            full_text
        ):

            return {

                "accepted": False,

                "confidence": 0,

                "classification":
                    "FOREIGN REMOTE",

                "location":
                    "FOREIGN",

                "reason":
                    "Remote job restricted "
                    "to another country",

            }


        # Remote is acceptable ONLY if Bangladesh
        # is explicitly mentioned.

        if not bd_locations:

            return {

                "accepted": False,

                "confidence": 0,

                "classification":
                    "REMOTE UNKNOWN",

                "location":
                    "UNKNOWN",

                "reason":
                    "Remote but Bangladesh "
                    "eligibility not confirmed",

            }


    # ========================================================
    # STEP 8
    # NON-REMOTE JOBS
    # ========================================================

    if not remote:

        if not bd_locations:

            return {

                "accepted": False,

                "confidence": 0,

                "classification":
                    "LOCATION UNKNOWN",

                "location":
                    "UNKNOWN",

                "reason":
                    "No Bangladesh job "
                    "location detected",

            }


    # ========================================================
    # STEP 9
    # CONFIDENCE
    # ========================================================

    confidence = 0


    # AI/ML
    confidence += min(
        len(ai_matches) * 10,
        30
    )


    # Hiring signal
    confidence += min(
        len(hiring_matches) * 10,
        30
    )


    # Bangladesh
    if bd_locations:

        confidence += 30


    # Fresher
    if any(
        keyword in full_text
        for keyword in FRESHER_KEYWORDS
    ):

        confidence += 10


    # Remote
    if remote:

        confidence += 5


    confidence = min(
        confidence,
        100
    )


    # ========================================================
    # FINAL ACCEPTANCE
    # ========================================================

    if confidence < 60:

        return {

            "accepted": False,

            "confidence":
                confidence,

            "classification":
                "LOW CONFIDENCE",

            "location":
                "UNKNOWN",

            "reason":
                "Insufficient evidence",

        }


    return {

        "accepted": True,

        "confidence":
            confidence,

        "classification":
            "BANGLADESH AI/ML JOB",

        "location":
            "BANGLADESH",

        "reason":
            "Verified Bangladesh "
            "AI/ML hiring signal",

    }


# ============================================================
# SERPER SEARCH
# ============================================================

def serper_search(query):

    api_key = os.environ.get(
        "SERPER_API_KEY"
    )


    if not api_key:

        print(
            "ERROR: SERPER_API_KEY "
            "is missing."
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

        # Search approximately last month
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
# FACEBOOK SEARCH QUERIES
# ============================================================

FACEBOOK_QUERIES = [

    'site:facebook.com "AI Engineer" "Bangladesh" hiring',

    'site:facebook.com "AI Engineer" "Dhaka" hiring',

    'site:facebook.com "Machine Learning Engineer" "Bangladesh" hiring',

    'site:facebook.com "Machine Learning Intern" "Bangladesh"',

    'site:facebook.com "Machine Learning Intern" "Dhaka"',

    'site:facebook.com "AI Intern" "Bangladesh"',

    'site:facebook.com "AI Internship" "Dhaka"',

    'site:facebook.com "AI Trainee" "Bangladesh"',

    'site:facebook.com "Machine Learning Trainee" "Bangladesh"',

    'site:facebook.com "Junior AI Engineer" "Bangladesh"',

    'site:facebook.com "Junior Machine Learning" "Bangladesh"',

    'site:facebook.com "AI Research Intern" "Bangladesh"',

    'site:facebook.com "AI Research Assistant" "Bangladesh"',

    'site:facebook.com "Computer Vision Intern" "Bangladesh"',

    'site:facebook.com "NLP Intern" "Bangladesh"',

    'site:facebook.com "Generative AI Intern" "Bangladesh"',

    'site:facebook.com/groups "AI jobs" "Bangladesh"',

    'site:facebook.com/groups "AI internship" "Bangladesh"',

    'site:facebook.com/groups "machine learning jobs" "Bangladesh"',

]


# ============================================================
# COLLECT FACEBOOK JOBS
# ============================================================

def collect_facebook_jobs():

    print()
    print("=" * 70)
    print("STAGE 2: STRICT FACEBOOK SEARCH")
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


        results = serper_search(
            query
        )


        print(
            f"Search results: "
            f"{len(results)}"
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


            # Only Facebook
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


            analysis = classify_facebook_post(
                title,
                snippet
            )


            if not analysis["accepted"]:

                print()
                print(
                    "  ❌ REJECTED:"
                )

                print(
                    f"     {title}"
                )

                print(
                    f"     Reason: "
                    f"{analysis['reason']}"
                )

                continue


            print()
            print(
                "  ✅ ACCEPTED:"
            )

            print(
                f"     {title}"
            )

            print(
                f"     Location: "
                f"{analysis['location']}"
            )

            print(
                f"     Confidence: "
                f"{analysis['confidence']}"
            )


            combined_text = (

                title
                + " "
                + snippet

            )


            job = {

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
                    if contains_remote(
                        combined_text
                    )
                    else "On-site/Unspecified",

                "search_term":
                    query,

                "snippet":
                    snippet,

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
                        "confidence"
                    ],

                "location_verification":
                    analysis[
                        "location"
                    ],

                "post_classification":
                    analysis[
                        "classification"
                    ],

            }


            facebook_jobs.append(
                job
            )


    print()
    print(
        f"Accepted Facebook jobs: "
        f"{len(facebook_jobs)}"
    )


    if not facebook_jobs:

        return []


    return [
        pd.DataFrame(
            facebook_jobs
        )
    ]


# ============================================================
# JOB BOARD SEARCH
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


JOB_BOARD_SITES = [

    "linkedin",
    "indeed",
    "google",

]


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

                site_name=
                    JOB_BOARD_SITES,

                search_term=
                    search_term,

                location=
                    LOCATION,

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
                    f"Raw results: "
                    f"{len(jobs)}"
                )


                jobs[
                    "search_term"
                ] = search_term


                all_jobs.append(
                    jobs
                )


            else:

                print(
                    "No results."
                )


        except Exception as e:

            print(
                f"Search failed: {e}"
            )

            continue


    return all_jobs


# ============================================================
# FILTER JOB BOARD RESULTS
# ============================================================

def filter_job_board_jobs(
    dataframes
):

    if not dataframes:

        return []


    jobs = pd.concat(
        dataframes,
        ignore_index=True
    )


    print()
    print(
        f"Raw job-board jobs: "
        f"{len(jobs)}"
    )


    # ========================================================
    # AI/ML TITLE FILTER
    # ========================================================

    before = len(jobs)


    jobs = jobs[
        jobs["title"].apply(
            is_ai_ml_title
        )
    ].copy()


    print(
        f"Non-AI/ML removed: "
        f"{before - len(jobs)}"
    )


    # ========================================================
    # REMOVE SENIOR JOBS
    # ========================================================

    before = len(jobs)


    def senior_title(title):

        title = normalize_text(
            title
        )

        return any(
            keyword in title
            for keyword in SENIOR_KEYWORDS
        )


    jobs = jobs[
        ~jobs["title"].apply(
            senior_title
        )
    ].copy()


    print(
        f"Senior jobs removed: "
        f"{before - len(jobs)}"
    )


    # ========================================================
    # LOCATION FILTER
    # ========================================================

    before = len(jobs)


    def valid_job_board_location(
        location
    ):

        location = normalize_text(
            location
        )


        if not location:

            # JobSpy sometimes returns blank
            # location. Since your target is
            # Bangladesh, don't accept it.
            return False


        bd = any(
            keyword in location
            for keyword in BANGLADESH_LOCATIONS
        )


        foreign = any(
            keyword in location
            for keyword in FOREIGN_LOCATIONS
        )


        if foreign:

            return False


        return bd


    jobs = jobs[
        jobs["location"].apply(
            valid_job_board_location
        )
    ].copy()


    print(
        f"Non-Bangladesh jobs removed: "
        f"{before - len(jobs)}"
    )


    return [
        jobs
    ] if not jobs.empty else []


# ============================================================
# PREPARE ALL JOBS
# ============================================================

def prepare_jobs(
    dataframes
):

    if not dataframes:

        return pd.DataFrame()


    jobs = pd.concat(
        dataframes,
        ignore_index=True
    )


    if "job_url" not in jobs.columns:

        jobs["job_url"] = ""


    if "title" not in jobs.columns:

        jobs["title"] = ""


    if "company" not in jobs.columns:

        jobs["company"] = ""


    if "location" not in jobs.columns:

        jobs["location"] = ""


    if "date_posted" not in jobs.columns:

        jobs["date_posted"] = ""


    if "site" not in jobs.columns:

        jobs["site"] = ""


    if "job_type" not in jobs.columns:

        jobs["job_type"] = ""


    if "search_term" not in jobs.columns:

        jobs["search_term"] = ""


    if "snippet" not in jobs.columns:

        jobs["snippet"] = ""


    if "fresher_friendly" not in jobs.columns:

        jobs["fresher_friendly"] = ""


    if "ai_ml_relevance" not in jobs.columns:

        jobs["ai_ml_relevance"] = ""


    if "facebook_confidence" not in jobs.columns:

        jobs["facebook_confidence"] = ""


    if "location_verification" not in jobs.columns:

        jobs["location_verification"] = ""


    if "post_classification" not in jobs.columns:

        jobs["post_classification"] = ""


    # ========================================================
    # JOB IDS
    # ========================================================

    jobs["job_id"] = jobs.apply(
        create_job_id,
        axis=1
    )


    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    before = len(jobs)


    jobs = jobs.drop_duplicates(
        subset=["job_id"]
    )


    print(
        f"Duplicates removed: "
        f"{before - len(jobs)}"
    )


    # ========================================================
    # FRESHER
    # ========================================================

    jobs[
        "fresher_friendly"
    ] = jobs.apply(

        lambda row:

        clean_text(
            row.get(
                "fresher_friendly"
            )
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


    # ========================================================
    # AI/ML RELEVANCE
    # ========================================================

    jobs[
        "ai_ml_relevance"
    ] = jobs.apply(

        lambda row:

        clean_text(
            row.get(
                "ai_ml_relevance"
            )
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
# REMOVE FACEBOOK POSTS OLDER THAN 30 DAYS
# ============================================================

def remove_old_facebook_jobs():

    if WIPE_SHEET_ON_START:

        return


    print()
    print(
        "Checking expired Facebook jobs..."
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

        return


    now = datetime.now(
        timezone.utc
    )


    delete_rows = []


    formats = [

        "%Y-%m-%d",

        "%Y-%m-%d %H:%M",

        "%Y-%m-%d %H:%M UTC",

        "%Y-%m-%dT%H:%M:%S",

        "%Y-%m-%dT%H:%M:%S.%f",

    ]


    for row_number, row in enumerate(
        rows[1:],
        start=2
    ):

        if len(row) <= source_index:

            continue


        source = normalize_text(
            row[source_index]
        )


        if source != "facebook":

            continue


        date_value = ""


        if (
            len(row)
            > date_posted_index
        ):

            date_value = clean_text(
                row[
                    date_posted_index
                ]
            )


        if not date_value:

            if (
                len(row)
                > date_found_index
            ):

                date_value = clean_text(
                    row[
                        date_found_index
                    ]
                )


        parsed_date = None


        for fmt in formats:

            try:

                parsed_date = (
                    datetime.strptime(
                        date_value,
                        fmt
                    ).replace(
                        tzinfo=timezone.utc
                    )
                )

                break

            except ValueError:

                continue


        if parsed_date is None:

            continue


        age_days = (

            now - parsed_date
        ).total_seconds() / 86400


        if (
            age_days
            > FACEBOOK_RETENTION_DAYS
        ):

            delete_rows.append(
                row_number
            )


    for row_number in reversed(
        delete_rows
    ):

        worksheet.delete_rows(
            row_number
        )


    print(
        f"Removed "
        f"{len(delete_rows)} "
        f"old Facebook jobs."
    )


# ============================================================
# EXISTING IDS
# ============================================================

def get_existing_ids():

    rows = worksheet.get_all_values()


    if len(rows) <= 1:

        return set()


    return {

        clean_text(row[0])

        for row in rows[1:]

        if row

    }


# ============================================================
# UPLOAD
# ============================================================

def upload_jobs(jobs):

    if jobs.empty:

        print()
        print(
            "No jobs to upload."
        )

        return 0


    existing_ids = (
        get_existing_ids()
    )


    now = datetime.now(
        timezone.utc
    ).strftime(
        "%Y-%m-%d %H:%M UTC"
    )


    rows_to_add = []

    seen = set()


    for _, job in jobs.iterrows():

        job_id = clean_text(
            job.get(
                "job_id"
            )
        )


        if not job_id:

            continue


        if job_id in existing_ids:

            continue


        if job_id in seen:

            continue


        seen.add(
            job_id
        )


        rows_to_add.append([

            job_id,

            clean_text(
                job.get(
                    "title"
                )
            ),

            clean_text(
                job.get(
                    "company"
                )
            ),

            clean_text(
                job.get(
                    "location"
                )
            ),

            clean_text(
                job.get(
                    "date_posted"
                )
            ),

            clean_text(
                job.get(
                    "job_url"
                )
            ),

            clean_text(
                job.get(
                    "site"
                )
            ),

            clean_text(
                job.get(
                    "job_type"
                )
            ),

            now,

            "To Apply",

            clean_text(
                job.get(
                    "fresher_friendly"
                )
            ),

            clean_text(
                job.get(
                    "ai_ml_relevance"
                )
            ),

            clean_text(
                job.get(
                    "search_term"
                )
            ),

            clean_text(
                job.get(
                    "location_verification"
                )
            ),

            clean_text(
                job.get(
                    "facebook_confidence"
                )
            ),

            clean_text(
                job.get(
                    "post_classification"
                )
            ),

            clean_text(
                job.get(
                    "snippet"
                )
            ),

        ])


    if not rows_to_add:

        print()
        print(
            "No NEW jobs."
        )

        return 0


    worksheet.append_rows(

        rows_to_add,

        value_input_option=
            "USER_ENTERED"

    )


    print()
    print(
        f"Added "
        f"{len(rows_to_add)} "
        f"new jobs."
    )


    return len(rows_to_add)


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("AI JOB HUNTER")
    print("BANGLADESH AI/ML EDITION")
    print("=" * 70)


    # ========================================================
    # SHEET
    # ========================================================

    setup_sheet()


    # ========================================================
    # OLD FACEBOOK JOB CLEANUP
    # ========================================================

    remove_old_facebook_jobs()


    # ========================================================
    # STAGE 1
    # ========================================================

    raw_job_boards = (
        collect_job_board_jobs()
    )


    filtered_job_boards = (
        filter_job_board_jobs(
            raw_job_boards
        )
    )


    # ========================================================
    # STAGE 2
    # ========================================================

    facebook_jobs = (
        collect_facebook_jobs()
    )


    # ========================================================
    # COMBINE
    # ========================================================

    all_data = (
        filtered_job_boards
        + facebook_jobs
    )


    # ========================================================
    # PREPARE
    # ========================================================

    jobs = prepare_jobs(
        all_data
    )


    # ========================================================
    # UPLOAD
    # ========================================================

    new_jobs = upload_jobs(
        jobs
    )


    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 70)
    print("COMPLETED")
    print("=" * 70)

    print(
        f"Processed: "
        f"{len(jobs)}"
    )

    print(
        f"New jobs added: "
        f"{new_jobs}"
    )

    print()

    print(
        "Filters active:"
    )

    print(
        "  ✓ AI/ML role required"
    )

    print(
        "  ✓ Bangladesh location required"
    )

    print(
        "  ✓ Foreign locations rejected"
    )

    print(
        "  ✓ Pune rejected"
    )

    print(
        "  ✓ Colombo rejected"
    )

    print(
        "  ✓ US-only rejected"
    )

    print(
        "  ✓ Foreign remote jobs rejected"
    )

    print(
        "  ✓ Job seekers rejected"
    )

    print(
        "  ✓ Courses/training rejected"
    )

    print(
        "  ✓ Events/webinars rejected"
    )

    print(
        "  ✓ Senior jobs rejected"
    )

    print(
        "  ✓ Intern/trainee/junior detected"
    )

    print(
        "  ✓ Duplicate jobs removed"
    )

    print(
        "  ✓ Old Facebook posts removed"
    )

    print("=" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()
