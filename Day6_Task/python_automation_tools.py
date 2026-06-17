
# ============================================
# INSTALL REQUIRED LIBRARIES
# ============================================

!pip install requests beautifulsoup4 schedule apscheduler watchdog -q


# ============================================
# IMPORT REQUIRED MODULES
# ============================================

import os
import csv
import time
import shutil
import requests
import smtplib

from pathlib import Path
from datetime import datetime

from bs4 import BeautifulSoup
from email.mime.text import MIMEText

import schedule

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


# ============================================
# FILE ORGANIZER AUTOMATION
# ============================================

EXT_MAP = {
    ".pdf": "PDFs",
    ".jpg": "Images",
    ".png": "Images",
    ".csv": "Data",
    ".xlsx": "Data",
    ".mp4": "Videos",
}

def organise(folder):

    src = Path(folder)

    for file in src.iterdir():

        if file.is_file():

            destination = src / EXT_MAP.get(
                file.suffix.lower(),
                "Other"
            )

            destination.mkdir(exist_ok=True)

            shutil.move(
                str(file),
                destination / file.name
            )

            print(f"Moved {file.name} -> {destination.name}/")


# RUN FILE ORGANIZER

organise("/content/sample_data")


# ============================================
# WEB SCRAPING AUTOMATION
# ============================================

def scrape_quotes():

    url = "https://quotes.toscrape.com"

    response = requests.get(
        url,
        timeout=10
    )

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    quotes = []

    for q in soup.select(".quote")[:5]:

        quotes.append({
            "text": q.find(
                "span",
                class_="text"
            ).text,

            "author": q.find(
                "small"
            ).text,

            "scraped_at": datetime.now().isoformat(),
        })

    return quotes


# ============================================
# SAVE DATA TO CSV
# ============================================

def save_to_csv(rows, path="quotes.csv"):

    file_exists = os.path.isfile(path)

    with open(
        path,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "text",
                "author",
                "scraped_at"
            ]
        )

        if not file_exists:
            writer.writeheader()

        writer.writerows(rows)

    print(f"Saved {len(rows)} rows into {path}")


# RUN WEB SCRAPER

data = scrape_quotes()

save_to_csv(data)


# ============================================
# EMAIL AUTOMATION
# ============================================

def send_alert(
    subject,
    body,
    to,
    gmail_user,
    app_password
):

    try:

        msg = MIMEText(body)

        msg["Subject"] = subject
        msg["From"] = gmail_user
        msg["To"] = to

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465
        ) as server:

            server.login(
                gmail_user,
                app_password
            )

            server.send_message(msg)

        print("Email sent successfully.")

    except Exception as e:

        print("Email failed.")
        print("Error:", e)


# ============================================
# EMAIL EXAMPLE
# ============================================

# Uncomment and use your Gmail App Password

# send_alert(
#     subject="Automation Completed",
#     body="Web scraping completed successfully.",
#     to="receiver@gmail.com",
#     gmail_user="yourgmail@gmail.com",
#     app_password="your_gmail_app_password"
# )


# ============================================
# SCHEDULED AUTOMATION JOBS
# ============================================

def job_scrape():

    data = scrape_quotes()

    save_to_csv(data)

    print(
        f"[{datetime.now():%H:%M:%S}] "
        "Scraping completed"
    )


def job_report():

    print(
        f"[{datetime.now():%H:%M:%S}] "
        "Daily report generated"
    )


# ============================================
# SCHEDULE LIBRARY AUTOMATION
# ============================================

schedule.every(10).seconds.do(job_scrape)

schedule.every().day.at("08:00").do(job_report)

print("Scheduler Started...")


end_time = time.time() + 35

while time.time() < end_time:

    schedule.run_pending()

    time.sleep(1)

print("Scheduler Stopped.")


# ============================================
# APSCHEDULER AUTOMATION
# ============================================

scheduler = BackgroundScheduler()

scheduler.add_job(
    job_scrape,
    trigger="interval",
    seconds=15,
    id="scraper_job"
)

scheduler.add_job(
    job_report,
    CronTrigger(
        day_of_week="mon-fri",
        hour=7,
        minute=30
    ),
    id="daily_report_job"
)

scheduler.start()

print("APScheduler Running...\n")

for job in scheduler.get_jobs():

    print(f"Job ID: {job.id}")

    print(
        f"Next Run Time: "
        f"{job.next_run_time}\n"
    )

time.sleep(40)

scheduler.shutdown()

print("APScheduler Stopped.")


# ============================================
# PROJECT COMPLETED
# ============================================

print("\nPython Automation Project Completed Successfully.")

# ============================================
# ARGPARSE EXAMPLE
# ============================================

import argparse

parser = argparse.ArgumentParser()

parser.add_argument(
    "--name",
    type=str,
    default="Akash"
)

args = parser.parse_args(args=[])

print(f"Hello, {args.name}")

# ============================================
# SUBPROCESS EXAMPLE
# ============================================

import subprocess

result = subprocess.run(
    ["ls", "/content"],
    capture_output=True,
    text=True
)

print("Subprocess Output:\n")

print(result.stdout)

# ============================================
# CRON EXAMPLE
# ============================================

cron_expression = "0 8 * * *"

print("Cron Schedule Example:")

print(f"Runs daily at 08:00 AM -> {cron_expression}")

