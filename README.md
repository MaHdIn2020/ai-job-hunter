# 🤖 AI Job Hunter

> An automated AI/ML job discovery system that continuously searches for relevant jobs in Bangladesh and sends them to Google Sheets for easy tracking.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Automated-black?logo=githubactions)
![Google Sheets](https://img.shields.io/badge/Google%20Sheets-Integrated-green?logo=googlesheets)
![Facebook](https://img.shields.io/badge/Facebook-Job%20Search-1877F2?logo=facebook)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📌 What is this?

**AI Job Hunter** is an automated job-search system designed primarily for students, fresh graduates, and entry-level candidates looking for AI/ML or teaching/instructor positions.

The system automatically searches job sources, filters the results, removes irrelevant jobs and duplicates, and stores the useful results in a Google Sheet. The main targets are:

**🤖 AI / ML / Data Positions:**
- AI Engineer, Machine Learning Engineer, ML Engineer, Artificial Intelligence Engineer
- AI Intern, ML Intern, AI Trainee, ML Trainee
- Deep Learning Engineer, Computer Vision Engineer, NLP Engineer
- Generative AI Engineer, LLM Engineer
- AI Research Assistant, AI Research Intern
- Data Scientist, Data Science Intern, Data Analyst

**👨‍🏫 Teaching / Instructor Positions:**
- Coding Instructor, Programming Instructor, Programming Trainer, Coding Teacher
- Computer Science Instructor, IT Instructor, IT Trainer, Technology Instructor
- Software Instructor, Programming Mentor, Coding Mentor, Computer Instructor
- Computer Science Teacher, STEM Instructor, Robotics Instructor
- Python Instructor, C++ Instructor, Java Instructor
- Web Development Instructor, Software Development Instructor
- AI Instructor, Machine Learning Instructor
- Junior Coding Instructor, Coding Instructor Intern
- AI Teaching Assistant, Programming Teaching Assistant, Computer Science Teaching Assistant

The main target is AI/ML jobs, teaching/instructor positions, internships and trainee positions in Bangladesh, especially Dhaka.

---

## 🙏 Acknowledgements

This project is built using several open-source tools and APIs.

### 🔎 JobSpy

A major part of the job-board discovery system is powered by **JobSpy**, an open-source Python library for aggregating job listings from multiple job boards.

- Repository: https://github.com/speedyapply/JobSpy
- Package: `python-jobspy`
- License: MIT
- Original author/maintainer: Cullen Watson

This project does not claim ownership of JobSpy or its source code. A huge thank you to the JobSpy contributors for making multi-source job discovery much easier.

### 🌐 Serper

The Facebook/public-web discovery component uses **Serper** to query Google search results. Serper is used to discover publicly indexed pages and posts that may contain relevant job opportunities.

- Website: https://serper.dev/
- Service: Google Search API

This project is not affiliated with or endorsed by Serper.

### 📊 Google Sheets API

Google Sheets is used as the storage and job-tracking layer. The project uses Google's APIs to create/update spreadsheet data, store discovered jobs, remove duplicates, remove outdated Facebook entries, and maintain application status.

- Documentation: https://developers.google.com/workspace/sheets/api

This project is not affiliated with or endorsed by Google.

---

## ✨ Features

### 🔎 Automated Job Searching
The system searches for multiple AI/ML-related and teaching-related job titles instead of relying on a single search query. This includes Machine Learning Engineer, Machine Learning Intern, AI Engineer, AI Intern, AI Trainee, Artificial Intelligence Engineer, Deep Learning Engineer, Computer Vision Engineer, NLP Engineer, AI Research Intern, Machine Learning Research Assistant, Generative AI Intern, LLM Engineer, Coding Instructor, Programming Instructor, IT Trainer, Computer Science Instructor, and many more.

### 🇧🇩 Bangladesh-Focused Filtering
The system is specifically designed to prioritize jobs in Bangladesh. It recognizes locations such as Bangladesh, Dhaka, Chattogram, Chittagong, Sylhet, Rajshahi, Khulna, Rangpur, Mymensingh, Gazipur, Narayanganj, Savar, Uttara, Mirpur, Gulshan, and Banani. Foreign locations like Pune India, Colombo Sri Lanka, New York USA, London UK, and Toronto Canada are filtered out.

### 📘 Facebook Job Discovery
One of the main goals of this project is finding jobs that may not appear on traditional job portals. The system uses search-engine queries to discover publicly indexed Facebook posts and groups containing potential job opportunities using queries like AI Engineer Bangladesh hiring, AI Intern Dhaka, Machine Learning Intern Bangladesh, AI Trainee Bangladesh, Machine Learning Jobs Bangladesh, AI Research Intern Bangladesh, Coding Instructor Bangladesh, and Programming Trainer Dhaka.

**Important:** This project does not directly scrape private Facebook content. It searches publicly indexed Facebook pages, posts and groups through a search API. Facebook search results can therefore vary depending on what search engines have indexed.

### 🛡️ Strict Facebook Filtering
Facebook contains many posts that look like job advertisements but aren't actually useful job opportunities. The system therefore applies multiple filters:

**1. Employer vs Job Seeker:** The system attempts to reject posts such as "I am looking for a job," "I am seeking an AI job," "Fresh graduate looking for opportunities," and "Please help me find a job." These are job seekers, not employers.

**2. Actual Hiring Signal:** The system looks for signals such as We are hiring, We're hiring, We are looking for, Job opening, Vacancy, Open position, Join our team, Recruiting, Apply now, Send your CV, Submit your resume, and Applications are open.

**3. AI/ML or Teaching Relevance:** The actual role must contain AI/ML-related terminology like Machine Learning Engineer, AI Engineer, AI Intern, ML Intern, Deep Learning, Computer Vision, NLP, Generative AI, LLM, AI Research OR teaching-related terminology like Coding Instructor, Programming Instructor, IT Trainer, Computer Science Instructor, Teaching Assistant, Mentor, or Trainer.

**4. Foreign Job Rejection:** A post mentioning Bangladesh does not automatically mean the job is in Bangladesh. For example, "We are hiring an AI Engineer in Pune, India. Bangladesh applicants can see our other opportunities" should be rejected. Similarly, "Remote AI Engineer - US Only" is rejected.

**5. Remote Job Verification:** Remote jobs are accepted only when there is reasonable evidence that applicants from Bangladesh are eligible. For example, "Remote - Bangladesh" or "Remote - applicants from Bangladesh welcome" can be accepted. But "Remote - US only" is rejected.

**6. Non-Job Content:** The system attempts to remove posts about Courses, Training, Workshops, Webinars, Seminars, Bootcamps, Certifications, Events, Hackathons, and Competitions.

**7. Senior Positions:** The project is designed mainly for students and fresh graduates. Senior/management positions are filtered out where possible including Senior AI Engineer, Lead ML Engineer, Principal ML Engineer, AI Engineering Manager, Director of AI, Head of AI, and Senior Instructor positions.

### 🎓 Fresher-Friendly Detection
The system also checks whether a position appears suitable for someone with limited professional experience. It looks for Intern, Internship, Trainee, Junior, Entry Level, Graduate, Fresh Graduate, Fresher, New Grad, Research Intern, Research Assistant, Teaching Assistant, and Assistant Instructor. The Google Sheet includes a "Fresher Friendly" column so you can prioritize these opportunities.

### 🧠 Human-in-the-Loop Feedback System

The project includes a feedback system that learns from your manual reviews:

**Review Status Column:** Instead of mixing job relevance with application progress, the system now has separate columns:

| Column | Purpose |
|--------|---------|
| Status | Application progress (To Apply, Applied, Assessment, Interview, Rejected, Offer) |
| Review Status | Job relevance (Pending Review, Relevant, Not Related) |

**How the Feedback Loop Works:**
Job scraper → Google Sheets → You review jobs → Mark "Not Related" → Next run learns → Improves filtering


When you mark a job as "Not Related", the system:
1. Saves the rejected job information to `data/rejected_jobs.json`
2. Removes it from your main Google Sheet
3. Uses it as a feedback pattern for future filtering

**Important:** The system learns patterns, not individual keywords. For example, if you reject "AI Product Manager" because you personally don't want it, the system won't learn "AI" as a negative keyword. Instead, it learns broader patterns like job categories you're not interested in.

### 📊 Google Sheets Integration
All accepted jobs are automatically added to Google Sheets. The sheet contains information including Job ID, Job Title, Company, Location, Date Posted, Job URL, Source (LinkedIn, Facebook, etc.), Job Type (Remote/On-site), Date Found, Status (To Apply, Applied, Assessment, Interview, Rejected, Offer), Review Status (Pending Review, Relevant, Not Related), Fresher Friendly, Relevance Score, Search Query, Location Verification, Facebook Confidence, Post Classification, and Snippet.

### ♻️ Duplicate Removal
The system generates a unique ID for every job. If the same job is found again during another search or another workflow run, it will not be added again.

### 🗑️ Old Facebook Posts
Facebook posts can remain searchable for a long time. To prevent the sheet from becoming full of outdated Facebook opportunities, the system removes Facebook entries older than 30 days. This retention period can be changed in `app.py` by modifying `FACEBOOK_RETENTION_DAYS = 30`.

### 🧹 Feedback-Based Removal
When you mark a job as "Not Related", it gets removed from the sheet on the next workflow run. The job data is preserved in `data/rejected_jobs.json` for future filtering improvements, keeping your Google Sheet clean while maintaining the feedback history.

### ⚙️ Automated GitHub Actions
The project can run automatically using GitHub Actions. The workflow can be configured to run every 6 hours using the cron schedule "0 */6 * * *". GitHub Actions uses UTC time. You can also manually run the workflow from GitHub → Actions → Job Search → Run workflow.

---

## 🏗️ Project Structure

A typical repository looks like: ai-job-hunter/ with subdirectories and files including app.py, requirements.txt, README.md, data/rejected_jobs.json, data/learned_patterns.json, and .github/workflows/job-search.yml

---

## 🚀 Setup

### 1. Fork or Clone the Repository

Clone the repository using: git clone https://github.com/YOUR_USERNAME/ai-job-hunter.git then move into the directory with cd ai-job-hunter

### 2. Install Python

This project uses Python 3.11. Python 3.11 is recommended because some dependencies may not work correctly with newer Python versions. Check your Python version with python --version

### 3. Install Dependencies

Install the required packages using: pip install -r requirements.txt. A typical requirements.txt contains: python-jobspy, gspread, google-auth, pandas, and requests

### 4. Create a Google Sheet

Create a new Google Sheet named for example "AI Job Hunter". Copy the Sheet ID from the URL. A Google Sheets URL looks like https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit. The value between /d/ and /edit is your GOOGLE_SHEET_ID

### 5. Create a Google Service Account

You need a Google Cloud service account so GitHub Actions can write to your Google Sheet. Go to Google Cloud Console and create a project. Then enable Google Sheets API. Create a Service Account. Create a JSON key for the service account and download the JSON credentials.

### 6. Share the Google Sheet

Open your Google Sheet. Click Share. Copy the service account email which usually looks similar to something@your-project.iam.gserviceaccount.com. Share the Google Sheet with that email and give it Editor permission. The service account email is not your personal Gmail address.

### 7. Add GitHub Secrets

Go to GitHub Repository → Settings → Secrets and variables → Actions → New repository secret. Add the following secrets: GOOGLE_CREDENTIALS: Paste the entire contents of your Google service-account JSON file. It should look similar to: {"type":"service_account","project_id":"your-project","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\\n...","client_email":"your-service-account@your-project.iam.gserviceaccount.com","client_id":"...","auth_uri":"...","token_uri":"..."}. Do not commit this JSON file to GitHub. GOOGLE_SHEET_ID: Create another secret with value your_google_sheet_id

### 8. Add Serper API Key

The project uses Serper to discover publicly indexed Facebook results. Create an API key from Serper. Then add a GitHub secret named SERPER_API_KEY and paste your API key as the value. Never put the API key directly inside app.py and never commit it to GitHub. Use GitHub Secrets instead.

### 9. GitHub Actions Environment

Your workflow should provide the secrets to Python. Example: - name: Run job scraper with env: GOOGLE_CREDENTIALS_JSON: ${{ secrets.GOOGLE_CREDENTIALS }}, GOOGLE_SHEET_ID: ${{ secrets.GOOGLE_SHEET_ID }}, SERPER_API_KEY: ${{ secrets.SERPER_API_KEY }} and run: python app.py

### 10. Automatic Scheduling

Example workflow: name: Job Search, on: workflow_dispatch and schedule with cron: "0 */6 * * *", jobs: search-jobs runs-on: ubuntu-latest with steps including checkout repository using actions/checkout@v4, set up Python using actions/setup-python@v5 with python-version: "3.11", install dependencies with python -m pip install --upgrade pip and pip install -r requirements.txt, and run job scraper with the environment variables GOOGLE_CREDENTIALS_JSON, GOOGLE_SHEET_ID, and SERPER_API_KEY

---

## ⚠️ Important: First Run

The current app.py contains WIPE_SHEET_ON_START = True. This is intentional if you want to clean your existing sheet after installing the new filtering system. Run it once. After the first successful run, change it to WIPE_SHEET_ON_START = False. Then commit and push the change. Otherwise, your scheduled GitHub Actions workflow will clear the entire sheet every 6 hours.

---

## 🧠 How the System Works

The system flow is: JOB SOURCES go through JobSpy for job boards and Serper for public Facebook/Web search. Serper returns Facebook results which go through strict filtering. Both JobSpy results and filtered Facebook results then go through initial filtering checking for AI/ML or Education/Instructor relevance, followed by Bangladesh Check, Fresher Check, Deduplication, and finally get written to Google Sheets. You then review jobs and mark them as either Relevant (kept in sheet) or Not Related (saved to feedback data and removed from sheet). On the next workflow execution, the system uses your feedback for personalized filtering.

---

## 🎯 Recommended Use

This project is particularly useful if you are a university student, a fresh graduate, looking for internships, looking for trainee positions, looking for junior AI/ML roles, interested in teaching/coding instructor positions, applying for multiple jobs every week, or tired of manually checking multiple job boards. Instead of checking several websites repeatedly, you can open your Google Sheet and review the collected opportunities.

---

## 📋 Suggested Application Workflow

The Google Sheet can be used as a simple job tracker with two types of statuses. Application Status includes: To Apply, Applied, Assessment, Interview, Rejected, and Offer. Review Status includes: Pending Review (default for new jobs), Relevant (you want to apply), and Not Related (not relevant to your goals). You can manually update both the Status and Review Status columns.

---

## 🔐 Security

Never commit the following to GitHub: Google service-account JSON, API keys, Passwords, Access tokens, and Private credentials. Use GitHub Secrets instead. Add secrets under Repository → Settings → Secrets and variables → Actions.

---

## ⚠️ Limitations

This project relies on external websites and search APIs. Therefore not every job on the internet will be found. Facebook search results depend on what search engines have indexed. Private posts and private groups cannot be accessed. Search engines may provide only a portion of a Facebook post, so the Facebook filtering system cannot guarantee perfect classification. JobSpy depends on the websites it supports and those websites can change their structure or anti-bot systems. Scheduled GitHub Actions jobs may occasionally run later than the exact scheduled time. The feedback system learns patterns but cannot perfectly understand context, so you should still review all jobs manually.

---

## 🛠️ Customization

You can customize the project directly in app.py. Change target location with LOCATION = "Dhaka, Bangladesh". Change Facebook retention period with FACEBOOK_RETENTION_DAYS = 30. Change number of jobs per search with RESULTS_PER_SEARCH = 15. Add AI/ML keywords by modifying AI_ML_KEYWORDS. Add teaching/instructor keywords by modifying TEACHING_KEYWORDS. Add Bangladesh locations by modifying BANGLADESH_LOCATIONS. Add foreign locations by modifying FOREIGN_LOCATIONS. Disable or enable feedback learning by modifying FEEDBACK_ENABLED = True.

---

## 🤝 Contributing

Contributions are welcome. If you find a false positive, a false negative, a broken job source, a missing keyword, a location filtering problem, or a useful new job source, feel free to open an issue or submit a pull request.

---

## 💡 Future Improvements

Possible future versions may include AI/LLM-based job classification, better Facebook post verification, more job boards, Telegram job groups, email notifications, WhatsApp notifications, automatic job scoring, resume-to-job matching, skill gap detection, company reputation scoring, application deadline detection, automatic daily/weekly reports, better location extraction, salary extraction, remote-job eligibility detection, job recommendation ranking, improved pattern learning from feedback, and support for more job categories.

---

## ⭐ Why this project?

Finding a job is often less about finding one job and more about finding enough relevant opportunities to apply to consistently. This project tries to automate the repetitive part: Search, Filter, Remove irrelevant jobs, Remove duplicates, Track opportunities, and Apply manually. The final application decision should still be made by the candidate. The feedback system helps the scraper get better over time based on your personal preferences.

---

## 📜 License

This project is released under the MIT License. You are free to use, modify and improve it according to the terms of the license.

---

## 👨‍💻 Author

Built as an automated AI/ML job-hunting project. If you find this project useful, consider giving the repository a star.

---

## ⭐ Star the Repository

If this project helped you automate your job search, consider starring the repository and sharing improvements with the community.
