import csv
from jobspy import scrape_jobs

jobs = scrape_jobs(
    site_name=["indeed", "linkedin", "bdjobs", "google"], # "glassdoor", "bayt", "naukri", 
    search_term="Machine Learning Engineer",
    google_search_term="software engineer jobs in dhaka, Bangladesh since this week",
    location="Dhaka, Bangladesh",
    results_wanted=20,
    hours_old=72,
    country_indeed='Bangladesh',
    
    # linkedin_fetch_description=True # gets more info such as description, direct job url (slower)
    # proxies=["208.195.175.46:65095", "208.195.175.45:65095", "localhost"],
)
print(jobs.to_string())