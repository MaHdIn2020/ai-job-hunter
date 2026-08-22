import csv
from jobspy import scrape_jobs

jobs = scrape_jobs(
    site_name=["indeed", "linkedin", "google"],
    search_term="machine learning engineer",
    location="Dhaka",
    results_wanted=20,
    hours_old=72
)

print(jobs.to_string())
