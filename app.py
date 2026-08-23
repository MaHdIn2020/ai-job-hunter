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

# Persistent feedback memory
FEEDBACK_FILE = "data/feedback.json"

# Keep FALSE during normal operation.
# TRUE will clear the entire Google Sheet.
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

    # Application status
    "Status",

    # Human review
    "Review Status",
    "Review Reason",

    # Automatic analysis
    "Fresher Friendly",
    "AI/ML Relevance",
    "Search Query",
    "Location Verification",
    "Facebook Confidence",
    "Post Classification",
    "Snippet",
]


# ============================================================
# REVIEW STATUS
# ============================================================

REVIEW_PENDING = "Pending Review"
REVIEW_RELEVANT = "Relevant"
REVIEW_NOT_RELATED = "Not Related"


# ============================================================
# REVIEW REASONS
# ============================================================

REVIEW_REASONS = [
    "Wrong Location",
    "Not AI/ML",
    "Not Instructor/Teaching",
    "Too Senior",
    "Wrong Job Type",
    "Seeking Job, Not Hiring",
    "Not a Job Post",
    "Duplicate",
    "Other",
]


# ============================================================
# APPLICATION STATUSES
# ============================================================

APPLICATION_STATUSES = [
    "To Apply",
    "Applied",
    "Assessment",
    "Interview",
    "Rejected",
    "Offer",
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

    "ai agent",
    "ai agents",
    "agentic ai",
    "generative ai engineer",

]


# ============================================================
# RELATED AI ROLES
# ============================================================

RELATED_AI_ROLES = [

    "data scientist",
    "data science intern",
    "data science trainee",

    "research assistant",
    "ai research assistant",
    "machine learning research assistant",

    "data analyst",
    "data analyst intern",

]


# ============================================================
# CODING / IT INSTRUCTOR KEYWORDS
# ============================================================

INSTRUCTOR_KEYWORDS = [

    "coding instructor",
    "coding trainer",
    "coding teacher",
    "coding mentor",

    "programming instructor",
    "programming trainer",
    "programming teacher",
    "programming mentor",

    "software instructor",
    "software trainer",

    "it instructor",
    "it trainer",
    "it teacher",

    "computer instructor",
    "computer trainer",

    "computer science instructor",
    "computer science teacher",
    "computer science trainer",

    "technology instructor",
    "technology trainer",

    "technical instructor",
    "technical trainer",

    "programming teaching assistant",
    "coding teaching assistant",
    "computer science teaching assistant",
    "teaching assistant programming",

    "ai instructor",
    "ai trainer",
    "ai teacher",

    "machine learning instructor",
    "machine learning trainer",
    "ml instructor",
    "ml trainer",

    "python instructor",
    "python trainer",

    "c++ instructor",
    "c++ trainer",

    "java instructor",
    "java trainer",

    "web development instructor",
    "web development trainer",

    "software development instructor",
    "software development trainer",

    "robotics instructor",
    "robotics trainer",

    "stem instructor",
    "stem trainer",

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
    "research intern",
    "research assistant",

    "teaching assistant",
    "junior instructor",
    "assistant instructor",
    "assistant trainer",

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
# JOB SEEKER SIGNALS
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
    "barishal",
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
# STRONG FOREIGN CITIES
# ============================================================

STRONG_FOREIGN_LOCATIONS = [

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
# FOREIGN REMOTE RESTRICTIONS
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
# TARGET JOB CATEGORY
# ============================================================

def detect_job_category(title, text):

    title = normalize_text(title)
    text = normalize_text(text)

    if any(
        keyword in title
        for keyword in INSTRUCTOR_KEYWORDS
    ):
        return "Coding / IT Instructor"

    if any(
        keyword in text
        for keyword in INSTRUCTOR_KEYWORDS
    ):
        return "Coding / IT Instructor"

    if any(
        keyword in title
        for keyword in AI_ML_KEYWORDS
    ):
        return "AI / ML"

    if any(
        keyword in text
        for keyword in AI_ML_KEYWORDS
    ):
        return "AI / ML"

    if any(
        keyword in text
        for keyword in RELATED_AI_ROLES
    ):
        return "AI / Data / Research"

    return ""


# ============================================================
# FEEDBACK MEMORY
# ============================================================

def ensure_feedback_directory():

    directory = os.path.dirname(
        FEEDBACK_FILE
    )

    if directory:
        os.makedirs(
            directory,
            exist_ok=True
        )


def default_feedback():

    return {
        "rejected_jobs": [],

        "rejected_by_reason": {
            reason: []
            for reason in REVIEW_REASONS
        },

        "learned_patterns": {
            reason: []
            for reason in REVIEW_REASONS
        },

        "rejected_locations": [],

        "statistics": {
            reason: 0
            for reason in REVIEW_REASONS
        },
    }


def load_feedback():

    ensure_feedback_directory()

    if not os.path.exists(
        FEEDBACK_FILE
    ):
        return default_feedback()

    try:

        with open(
            FEEDBACK_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if not isinstance(
            data,
            dict
        ):
            raise ValueError(
                "Invalid feedback format"
            )

        defaults = default_feedback()

        data.setdefault(
            "rejected_jobs",
            []
        )

        data.setdefault(
            "rejected_by_reason",
            {}
        )

        data.setdefault(
            "learned_patterns",
            {}
        )

        data.setdefault(
            "rejected_locations",
            []
        )

        data.setdefault(
            "statistics",
            {}
        )

        for reason in REVIEW_REASONS:

            data["rejected_by_reason"].setdefault(
                reason,
                []
            )

            data["learned_patterns"].setdefault(
                reason,
                []
            )

            data["statistics"].setdefault(
                reason,
                0
            )

        return data

    except Exception as e:

        print(
            f"Could not load feedback: {e}"
        )

        return default_feedback()


def save_feedback(feedback):

    ensure_feedback_directory()

    temporary_file = (
        FEEDBACK_FILE + ".tmp"
    )

    with open(
        temporary_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            feedback,
            file,
            indent=2,
            ensure_ascii=False
        )

    os.replace(
        temporary_file,
        FEEDBACK_FILE
    )


# ============================================================
# FEEDBACK TOKENIZATION
# ============================================================

GENERIC_FEEDBACK_WORDS = {

    "engineer",
    "engineering",
    "developer",
    "development",
    "software",
    "technology",
    "technical",

    "job",
    "jobs",
    "role",
    "position",
    "company",
    "team",

    "remote",
    "dhaka",
    "bangladesh",

    "intern",
    "internship",
    "junior",
    "trainee",
    "entry",
    "level",
    "graduate",
    "fresh",
    "fresher",

    "assistant",
    "research",

    "ai",
    "ml",
    "machine",
    "learning",
    "data",
    "science",
    "scientist",
    "artificial",
    "intelligence",

    "coding",
    "programming",
    "instructor",
    "trainer",
    "teacher",
    "mentor",

    "computer",
    "information",
    "it",

}


def tokenize_title(title):

    title = normalize_text(
        title
    )

    title = re.sub(
        r"[^a-z0-9+#. ]+",
        " ",
        title
    )

    tokens = title.split()

    return [
        token
        for token in tokens
        if len(token) >= 3
        and token not in GENERIC_FEEDBACK_WORDS
    ]


def generate_title_phrases(title):

    tokens = tokenize_title(
        title
    )

    phrases = []

    # Two-word phrases
    for i in range(
        len(tokens) - 1
    ):

        phrases.append(
            tokens[i]
            + " "
            + tokens[i + 1]
        )

    # Three-word phrases
    for i in range(
        len(tokens) - 2
    ):

        phrases.append(
            tokens[i]
            + " "
            + tokens[i + 1]
            + " "
            + tokens[i + 2]
        )

    return phrases


# ============================================================
# LEARN FROM FEEDBACK
# ============================================================

def learn_from_rejected_job(
    feedback,
    job_title,
    company,
    location,
    url,
    reason,
):

    reason = clean_text(
        reason
    )

    if reason not in REVIEW_REASONS:
        reason = "Other"

    normalized_title = normalize_text(
        job_title
    )

    normalized_url = normalize_text(
        url
    )

    normalized_company = normalize_text(
        company
    )

    normalized_location = normalize_text(
        location
    )

    if not normalized_title:
        return

    # --------------------------------------------------------
    # Avoid saving same rejection repeatedly
    # --------------------------------------------------------

    for rejected in feedback[
        "rejected_jobs"
    ]:

        old_url = normalize_text(
            rejected.get(
                "job_url",
                ""
            )
        )

        old_title = normalize_text(
            rejected.get(
                "job_title",
                ""
            )
        )

        old_company = normalize_text(
            rejected.get(
                "company",
                ""
            )
        )

        if (
            normalized_url
            and old_url
            == normalized_url
        ):
            return

        if (
            old_title
            == normalized_title
            and old_company
            == normalized_company
        ):
            return

    # --------------------------------------------------------
    # Save complete rejection example
    # --------------------------------------------------------

    rejection = {

        "job_title":
            clean_text(job_title),

        "company":
            clean_text(company),

        "location":
            clean_text(location),

        "job_url":
            clean_text(url),

        "reason":
            reason,

        "rejected_at":
            datetime.now(
                timezone.utc
            ).isoformat(),

    }

    feedback[
        "rejected_jobs"
    ].append(
        rejection
    )

    feedback[
        "rejected_by_reason"
    ].setdefault(
        reason,
        []
    )

    feedback[
        "rejected_by_reason"
    ][reason].append(
        rejection
    )

    feedback[
        "statistics"
    ][reason] = (
        feedback[
            "statistics"
        ].get(
            reason,
            0
        )
        + 1
    )

    # --------------------------------------------------------
    # WRONG LOCATION
    #
    # Learn the actual location separately.
    # We do NOT learn the title as a bad title.
    # --------------------------------------------------------

    if reason == "Wrong Location":

        if (
            normalized_location
            and normalized_location
            not in feedback[
                "rejected_locations"
            ]
        ):

            feedback[
                "rejected_locations"
            ].append(
                normalized_location
            )

    # --------------------------------------------------------
    # OTHER TITLE-BASED REASONS
    # --------------------------------------------------------

    if reason in [
        "Not AI/ML",
        "Too Senior",
        "Wrong Job Type",
        "Not Instructor/Teaching",
        "Seeking Job, Not Hiring",
        "Not a Job Post",
        "Other",
    ]:

        all_rejections = (
            feedback[
                "rejected_by_reason"
            ][reason]
        )

        title_counts = {}

        for item in all_rejections:

            item_title = normalize_text(
                item.get(
                    "job_title",
                    ""
                )
            )

            phrases = set(
                generate_title_phrases(
                    item_title
                )
            )

            for phrase in phrases:

                title_counts[
                    phrase
                ] = (
                    title_counts.get(
                        phrase,
                        0
                    )
                    + 1
                )

        learned = [

            phrase

            for phrase, count
            in title_counts.items()

            if count >= 2

        ]

        feedback[
            "learned_patterns"
        ][reason] = sorted(
            learned
        )


# ============================================================
# FEEDBACK REJECTION SCORE
# ============================================================

def feedback_rejection_score(
    title,
    company,
    text,
    location,
    feedback,
):

    title = normalize_text(
        title
    )

    company = normalize_text(
        company
    )

    text = normalize_text(
        text
    )

    location = normalize_text(
        location
    )

    # --------------------------------------------------------
    # Exact previously rejected job
    # --------------------------------------------------------

    for rejected in feedback[
        "rejected_jobs"
    ]:

        rejected_title = normalize_text(
            rejected.get(
                "job_title",
                ""
            )
        )

        rejected_company = normalize_text(
            rejected.get(
                "company",
                ""
            )
        )

        if (
            rejected_title
            and title
            == rejected_title
        ):

            if (
                not rejected_company
                or not company
                or rejected_company
                == company
            ):

                return 100

    # --------------------------------------------------------
    # WRONG LOCATION
    #
    # Only compare actual location information.
    # Do NOT reject a title because another rejected job
    # happened to have the same title.
    # --------------------------------------------------------

    wrong_location_examples = feedback.get(
        "rejected_locations",
        []
    )

    for bad_location in wrong_location_examples:

        if (
            bad_location
            and bad_location
            in location
        ):

            return 100

    # --------------------------------------------------------
    # CATEGORY-SPECIFIC LEARNING
    # --------------------------------------------------------

    # Not AI/ML
    for pattern in feedback[
        "learned_patterns"
    ].get(
        "Not AI/ML",
        []
    ):

        if pattern in title:

            return 70

    # Not Instructor/Teaching
    for pattern in feedback[
        "learned_patterns"
    ].get(
        "Not Instructor/Teaching",
        []
    ):

        if pattern in title:

            return 70

    # Too Senior
    for pattern in feedback[
        "learned_patterns"
    ].get(
        "Too Senior",
        []
    ):

        if pattern in title:

            return 60

    # Wrong Job Type
    for pattern in feedback[
        "learned_patterns"
    ].get(
        "Wrong Job Type",
        []
    ):

        if pattern in title:

            return 60

    # Seeking Job
    for pattern in feedback[
        "learned_patterns"
    ].get(
        "Seeking Job, Not Hiring",
        []
    ):

        if pattern in text:

            return 80

    # Not a Job Post
    for pattern in feedback[
        "learned_patterns"
    ].get(
        "Not a Job Post",
        []
    ):

        if pattern in title:

            return 80

    return 0


# ============================================================
# PROCESS HUMAN FEEDBACK
# ============================================================

def process_review_feedback():

    print()
    print("=" * 70)
    print("PROCESSING HUMAN FEEDBACK")
    print("=" * 70)

    rows = worksheet.get_all_values()

    if len(rows) <= 1:

        print(
            "No existing jobs to review."
        )

        return

    headers = rows[0]

    try:

        review_index = headers.index(
            "Review Status"
        )

        reason_index = headers.index(
            "Review Reason"
        )

        job_id_index = headers.index(
            "Job ID"
        )

        title_index = headers.index(
            "Job Title"
        )

        company_index = headers.index(
            "Company"
        )

        location_index = headers.index(
            "Location"
        )

        url_index = headers.index(
            "Job URL"
        )

    except ValueError as e:

        print(
            f"Required feedback column missing: {e}"
        )

        return

    feedback = load_feedback()

    rows_to_delete = []

    for row_number, row in enumerate(
        rows[1:],
        start=2
    ):

        if len(row) <= review_index:
            continue

        review_status = normalize_text(
            row[review_index]
        )

        if (
            review_status
            != normalize_text(
                REVIEW_NOT_RELATED
            )
        ):
            continue

        title = (
            row[title_index]
            if len(row) > title_index
            else ""
        )

        company = (
            row[company_index]
            if len(row) > company_index
            else ""
        )

        location = (
            row[location_index]
            if len(row) > location_index
            else ""
        )

        url = (
            row[url_index]
            if len(row) > url_index
            else ""
        )

        reason = (
            row[reason_index]
            if len(row) > reason_index
            else ""
        )

        reason = clean_text(
            reason
        )

        # If the user forgot to select a reason,
        # don't lose the feedback.
        if reason not in REVIEW_REASONS:

            reason = "Other"

        print()
        print(
            "❌ HUMAN REJECTION:"
        )

        print(
            f"   Title: {title}"
        )

        print(
            f"   Company: {company}"
        )

        print(
            f"   Location: {location}"
        )

        print(
            f"   Reason: {reason}"
        )

        learn_from_rejected_job(
            feedback,
            title,
            company,
            location,
            url,
            reason,
        )

        rows_to_delete.append(
            row_number
        )

    if rows_to_delete:

        save_feedback(
            feedback
        )

    # Delete from bottom to top
    for row_number in reversed(
        rows_to_delete
    ):

        worksheet.delete_rows(
            row_number
        )

    print()

    print(
        f"Human rejected jobs: "
        f"{len(rows_to_delete)}"
    )

    print(
        f"Total feedback examples: "
        f"{len(feedback['rejected_jobs'])}"
    )

    print()

    print(
        "Feedback statistics:"
    )

    for reason in REVIEW_REASONS:

        count = feedback[
            "statistics"
        ].get(
            reason,
            0
        )

        if count:

            print(
                f"  {reason}: {count}"
            )


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

        print(
            "Existing jobs deleted."
        )

        return

    existing_headers = worksheet.row_values(
        1
    )

    if not existing_headers:

        worksheet.update(
            "A1",
            [HEADERS]
        )

        return

    # Automatically add missing columns
    missing_headers = [

        header

        for header in HEADERS

        if header
        not in existing_headers

    ]

    if missing_headers:

        print()
        print(
            "Adding missing sheet columns:"
        )

        for header in missing_headers:

            print(
                f"  + {header}"
            )

            worksheet.update_cell(
                1,
                len(existing_headers) + 1,
                header
            )

            existing_headers.append(
                header
            )


# ============================================================
# JOB ID
# ============================================================

def create_job_id(row):

    url = clean_text(
        row.get(
            "job_url"
        )
    )

    if url:

        unique_value = (
            url.lower().strip()
        )

    else:

        unique_value = "|".join([
            clean_text(
                row.get(
                    "title"
                )
            ).lower(),

            clean_text(
                row.get(
                    "company"
                )
            ).lower(),

            clean_text(
                row.get(
                    "location"
                )
            ).lower(),

        ])

    return hashlib.sha256(
        unique_value.encode(
            "utf-8"
        )
    ).hexdigest()[:16]


# ============================================================
# TARGET TITLE FILTER
# ============================================================

def is_target_title(title):

    title = normalize_text(
        title
    )

    if not title:
        return False

    target_terms = [

        # AI / ML

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

        # Data / Research

        "data scientist",
        "data science intern",
        "data science trainee",

        "research assistant",
        "ai research assistant",
        "machine learning research assistant",

        "data analyst",
        "data analyst intern",

        # Instructor

        "coding instructor",
        "coding trainer",
        "coding teacher",
        "coding mentor",

        "programming instructor",
        "programming trainer",
        "programming teacher",
        "programming mentor",

        "it instructor",
        "it trainer",

        "computer instructor",
        "computer trainer",

        "computer science instructor",
        "computer science teacher",
        "computer science trainer",

        "technology instructor",
        "technology trainer",

        "technical instructor",
        "technical trainer",

        "programming teaching assistant",
        "coding teaching assistant",
        "computer science teaching assistant",

        "ai instructor",
        "ai trainer",

        "machine learning instructor",
        "machine learning trainer",

        "ml instructor",
        "ml trainer",

        "python instructor",
        "python trainer",

        "c++ instructor",
        "c++ trainer",

        "java instructor",
        "java trainer",

        "web development instructor",
        "web development trainer",

        "software development instructor",
        "software development trainer",

        "robotics instructor",
        "robotics trainer",

        "stem instructor",
        "stem trainer",

    ]

    return any(
        term in title
        for term in target_terms
    )


# ============================================================
# FRESHER CLASSIFICATION
# ============================================================

def classify_fresher(text):

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

def relevance_score(text):

    text = normalize_text(
        text
    )

    score = 0

    strong_terms = [

        "machine learning",
        "machine-learning",
        "artificial intelligence",

        "ai engineer",
        "machine learning engineer",
        "ml engineer",

        "coding instructor",
        "programming instructor",
        "it instructor",

    ]

    medium_terms = [

        "deep learning",
        "computer vision",
        "natural language processing",
        "nlp",

        "generative ai",
        "genai",
        "llm",

        "coding trainer",
        "programming trainer",
        "computer science instructor",

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

    text = normalize_text(
        text
    )

    bd_matches = [

        location

        for location
        in BANGLADESH_LOCATIONS

        if location in text

    ]

    foreign_matches = [

        location

        for location
        in FOREIGN_LOCATIONS

        if location in text

    ]

    return {

        "bangladesh":
            bd_matches,

        "foreign":
            foreign_matches,

    }


# ============================================================
# REMOTE CHECK
# ============================================================

def contains_remote(text):

    text = normalize_text(
        text
    )

    return any(
        keyword in text
        for keyword in REMOTE_KEYWORDS
    )


# ============================================================
# FOREIGN REMOTE CHECK
# ============================================================

def has_foreign_remote_restriction(text):

    text = normalize_text(
        text
    )

    return any(
        phrase in text
        for phrase
        in FOREIGN_REMOTE_RESTRICTIONS
    )


# ============================================================
# JOB SEEKER CHECK
# ============================================================

def is_job_seeker_post(text):

    text = normalize_text(
        text
    )

    return [

        keyword

        for keyword
        in APPLICANT_KEYWORDS

        if keyword in text

    ]


# ============================================================
# EMPLOYER SIGNAL
# ============================================================

def employer_hiring_signal(text):

    text = normalize_text(
        text
    )

    return [

        keyword

        for keyword
        in HIRING_KEYWORDS

        if keyword in text

    ]


# ============================================================
# FACEBOOK CLASSIFIER
# ============================================================

def classify_facebook_post(
    title,
    snippet,
    feedback,
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

    # --------------------------------------------------------
    # FEEDBACK
    # --------------------------------------------------------

    feedback_score = (
        feedback_rejection_score(
            title_text,
            "",
            full_text,
            "",
            feedback,
        )
    )

    if feedback_score >= 100:

        return {

            "accepted": False,

            "confidence": 0,

            "classification":
                "PREVIOUSLY REJECTED",

            "location":
                "REJECTED",

            "reason":
                "Previously rejected "
                "job pattern",

        }

    # --------------------------------------------------------
    # JOB SEEKER
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # EMPLOYER SIGNAL
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # TARGET CATEGORY
    # --------------------------------------------------------

    category = detect_job_category(
        title_text,
        full_text
    )

    if not category:

        return {

            "accepted": False,

            "confidence": 0,

            "classification":
                "NOT TARGET ROLE",

            "location":
                "REJECTED",

            "reason":
                "Not AI/ML/Data or "
                "Coding/IT education role",

        }

    # --------------------------------------------------------
    # NOISE
    # --------------------------------------------------------

    noise_matches = [

        keyword

        for keyword
        in NOISE_KEYWORDS

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

    # --------------------------------------------------------
    # SENIOR ROLE
    # --------------------------------------------------------

    senior_matches = [

        keyword

        for keyword
        in SENIOR_KEYWORDS

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

    # --------------------------------------------------------
    # LOCATION
    # --------------------------------------------------------

    location = analyze_location(
        full_text
    )

    bd_locations = location[
        "bangladesh"
    ]

    foreign_locations = location[
        "foreign"
    ]

    # Foreign location without Bangladesh
    if foreign_locations:

        if not bd_locations:

            return {

                "accepted": False,

                "confidence": 0,

                "classification":
                    "FOREIGN JOB",

                "location":
                    "FOREIGN",

                "reason":
                    "Job appears to be "
                    "outside Bangladesh",

            }

        # Strong foreign city wins even when
        # Bangladesh is mentioned elsewhere.
        if any(
            city in full_text
            for city
            in STRONG_FOREIGN_LOCATIONS
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

    # --------------------------------------------------------
    # REMOTE
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # NON-REMOTE
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------------

    confidence = 0

    category_matches = [

        keyword

        for keyword

        in (
            AI_ML_KEYWORDS
            + INSTRUCTOR_KEYWORDS
            + RELATED_AI_ROLES
        )

        if keyword in full_text

    ]

    confidence += min(
        len(category_matches) * 10,
        30
    )

    confidence += min(
        len(hiring_matches) * 10,
        30
    )

    if bd_locations:
        confidence += 30

    if any(
        keyword in full_text
        for keyword
        in FRESHER_KEYWORDS
    ):

        confidence += 10

    if remote:
        confidence += 5

    confidence = min(
        confidence,
        100
    )

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
            "BANGLADESH "
            + category.upper(),

        "location":
            "BANGLADESH",

        "reason":
            "Verified Bangladesh "
            "target-role hiring signal",

        "category":
            category,

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

    # AI / ML

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

    # Coding / IT education

    'site:facebook.com "Coding Instructor" "Bangladesh" hiring',
    'site:facebook.com "Coding Instructor" "Dhaka" hiring',

    'site:facebook.com "Programming Instructor" "Bangladesh" hiring',
    'site:facebook.com "Programming Trainer" "Bangladesh" hiring',

    'site:facebook.com "IT Instructor" "Bangladesh" hiring',
    'site:facebook.com "IT Trainer" "Bangladesh" hiring',

    'site:facebook.com "Computer Science Instructor" "Bangladesh"',

    'site:facebook.com "Python Instructor" "Bangladesh"',

    'site:facebook.com "Coding Mentor" "Bangladesh" hiring',

    'site:facebook.com "Teaching Assistant" "programming" "Bangladesh"',

    # Facebook groups

    'site:facebook.com/groups "AI jobs" "Bangladesh"',
    'site:facebook.com/groups "AI internship" "Bangladesh"',

    'site:facebook.com/groups "machine learning jobs" "Bangladesh"',

    'site:facebook.com/groups "programming jobs" "Bangladesh"',

    'site:facebook.com/groups "IT jobs" "Bangladesh"',

    'site:facebook.com/groups "coding instructor" "Bangladesh"',

]


# ============================================================
# COLLECT FACEBOOK JOBS
# ============================================================

def collect_facebook_jobs():

    print()
    print("=" * 70)
    print("STAGE 2: STRICT FACEBOOK SEARCH")
    print("=" * 70)

    feedback = load_feedback()

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

            if (
                "facebook.com"
                not in link.lower()
            ):

                continue

            normalized_url = (
                link.lower().strip()
            )

            if (
                normalized_url
                in seen_urls
            ):

                continue

            seen_urls.add(
                normalized_url
            )

            analysis = classify_facebook_post(
                title,
                snippet,
                feedback,
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
                f"     Category: "
                f"{analysis.get('category', '')}"
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
                    else
                    "On-site/Unspecified",

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
# JOB BOARD SEARCH TERMS
# ============================================================

SEARCH_TERMS = [

    # AI / ML

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

    "generative AI engineer",
    "generative AI intern",

    "LLM engineer",
    "LLM intern",

    # Data

    "data scientist",
    "data science intern",
    "data science trainee",

    "data analyst",
    "data analyst intern",

    # Coding / IT education

    "coding instructor",
    "coding trainer",

    "programming instructor",
    "programming trainer",

    "IT instructor",
    "IT trainer",

    "computer instructor",
    "computer science instructor",

    "computer science teacher",

    "programming mentor",
    "coding mentor",

    "Python instructor",
    "C++ instructor",

    "web development instructor",

    "software instructor",

    "AI instructor",

    "machine learning instructor",

    "robotics instructor",

]


# ============================================================
# JOB BOARD SITES
# ============================================================

JOB_BOARD_SITES = [
    "linkedin",
    "indeed",
    "google",
]


# ============================================================
# JOB BOARD SEARCH
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

    # --------------------------------------------------------
    # TARGET TITLE
    # --------------------------------------------------------

    before = len(jobs)

    jobs = jobs[
        jobs["title"].apply(
            is_target_title
        )
    ].copy()

    print(
        f"Non-target jobs removed: "
        f"{before - len(jobs)}"
    )

    # --------------------------------------------------------
    # SENIOR JOBS
    # --------------------------------------------------------

    before = len(jobs)

    def senior_title(title):

        title = normalize_text(
            title
        )

        return any(
            keyword in title
            for keyword
            in SENIOR_KEYWORDS
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

    # --------------------------------------------------------
    # LOCATION
    # --------------------------------------------------------

    before = len(jobs)

    def valid_job_board_location(
        location
    ):

        location = normalize_text(
            location
        )

        if not location:
            return False

        bd = any(
            keyword in location
            for keyword
            in BANGLADESH_LOCATIONS
        )

        foreign = any(
            keyword in location
            for keyword
            in FOREIGN_LOCATIONS
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

    required_defaults = {

        "job_url": "",
        "title": "",
        "company": "",
        "location": "",
        "date_posted": "",
        "site": "",
        "job_type": "",
        "search_term": "",
        "snippet": "",

        "fresher_friendly": "",
        "ai_ml_relevance": "",

        "facebook_confidence": "",
        "location_verification": "",
        "post_classification": "",

    }

    for column, default in (
        required_defaults.items()
    ):

        if column not in jobs.columns:

            jobs[column] = default

    # --------------------------------------------------------
    # JOB IDS
    # --------------------------------------------------------

    jobs["job_id"] = jobs.apply(
        create_job_id,
        axis=1
    )

    # --------------------------------------------------------
    # DUPLICATES
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
    # FEEDBACK FILTER
    # --------------------------------------------------------

    feedback = load_feedback()

    before = len(jobs)

    def not_rejected_by_feedback(
        row
    ):

        combined_text = (

            clean_text(
                row.get(
                    "title",
                    ""
                )
            )

            + " "

            + clean_text(
                row.get(
                    "snippet",
                    ""
                )
            )

        )

        score = feedback_rejection_score(

            row.get(
                "title",
                ""
            ),

            row.get(
                "company",
                ""
            ),

            combined_text,

            row.get(
                "location",
                ""
            ),

            feedback,

        )

        return score < 100

    jobs = jobs[
        jobs.apply(
            not_rejected_by_feedback,
            axis=1
        )
    ].copy()

    print(
        f"Previously rejected jobs removed: "
        f"{before - len(jobs)}"
    )

    # --------------------------------------------------------
    # FRESHER
    # --------------------------------------------------------

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
                row.get(
                    "title"
                )
            )

            + " "

            + clean_text(
                row.get(
                    "snippet"
                )
            )

        ),

        axis=1

    )

    # --------------------------------------------------------
    # RELEVANCE
    # --------------------------------------------------------

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
                row.get(
                    "title"
                )
            )

            + " "

            + clean_text(
                row.get(
                    "snippet"
                )
            )

        ),

        axis=1

    )

    return jobs


# ============================================================
# REMOVE OLD FACEBOOK JOBS
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

        clean_text(
            row[0]
        )

        for row in rows[1:]

        if row

    }


# ============================================================
# UPLOAD JOBS
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

            # Application status
            "To Apply",

            # Review status
            REVIEW_PENDING,

            # Review reason
            "",

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
    print("BANGLADESH AI/ML + CODING/IT EDITION")
    print("=" * 70)

    # --------------------------------------------------------
    # SHEET
    # --------------------------------------------------------

    setup_sheet()

    # --------------------------------------------------------
    # HUMAN FEEDBACK
    #
    # This happens BEFORE new scraping.
    #
    # If you previously marked:
    #
    # Review Status = Not Related
    #
    # and selected a Review Reason,
    # the system:
    #
    # 1. Stores the rejection
    # 2. Stores the reason
    # 3. Learns category-specific patterns
    # 4. Removes the job from the sheet
    #
    # --------------------------------------------------------

    process_review_feedback()

    # --------------------------------------------------------
    # OLD FACEBOOK CLEANUP
    # --------------------------------------------------------

    remove_old_facebook_jobs()

    # --------------------------------------------------------
    # STAGE 1
    # --------------------------------------------------------

    raw_job_boards = (
        collect_job_board_jobs()
    )

    filtered_job_boards = (
        filter_job_board_jobs(
            raw_job_boards
        )
    )

    # --------------------------------------------------------
    # STAGE 2
    # --------------------------------------------------------

    facebook_jobs = (
        collect_facebook_jobs()
    )

    # --------------------------------------------------------
    # COMBINE
    # --------------------------------------------------------

    all_data = (
        filtered_job_boards
        + facebook_jobs
    )

    # --------------------------------------------------------
    # PREPARE
    # --------------------------------------------------------

    jobs = prepare_jobs(
        all_data
    )

    # --------------------------------------------------------
    # UPLOAD
    # --------------------------------------------------------

    new_jobs = upload_jobs(
        jobs
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

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

    feedback = load_feedback()

    print(
        f"Feedback examples: "
        f"{len(feedback['rejected_jobs'])}"
    )

    print()

    print(
        "Feedback statistics:"
    )

    for reason in REVIEW_REASONS:

        count = feedback[
            "statistics"
        ].get(
            reason,
            0
        )

        if count:

            print(
                f"  {reason}: {count}"
            )

    print()

    print(
        "Target categories:"
    )

    print(
        "  ✓ AI / ML"
    )

    print(
        "  ✓ Data Science / Research"
    )

    print(
        "  ✓ Coding Instructor"
    )

    print(
        "  ✓ Programming Instructor"
    )

    print(
        "  ✓ IT Instructor"
    )

    print(
        "  ✓ IT Trainer"
    )

    print(
        "  ✓ Computer Science Instructor"
    )

    print(
        "  ✓ Coding / Programming Mentor"
    )

    print()

    print(
        "Filters active:"
    )

    print(
        "  ✓ Bangladesh location required"
    )

    print(
        "  ✓ Foreign locations rejected"
    )

    print(
        "  ✓ Foreign remote restrictions rejected"
    )

    print(
        "  ✓ Job seekers rejected"
    )

    print(
        "  ✓ Courses/training/events rejected"
    )

    print(
        "  ✓ Senior/management jobs rejected"
    )

    print(
        "  ✓ Fresher/intern/trainee detection"
    )

    print(
        "  ✓ Duplicate jobs removed"
    )

    print(
        "  ✓ Old Facebook jobs removed"
    )

    print(
        "  ✓ Reason-based feedback learning enabled"
    )

    print("=" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
