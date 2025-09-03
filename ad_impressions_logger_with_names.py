import requests
import time
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import json

API_URL = "https://api.adbutler.com/v2/reports?type=ad-item&period=day&preset=today&ad-items=523668188,523668181"
AD_ITEMS_URL = "https://api.adbutler.com/v2/ad-items?limit=100&id=523668188,523668181"
AUTH_HEADER = {
    "Authorization": "Basic 552ad1d70aa376a7e83f42fbfbac9283"
}

# Gmail SMTP credentials
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "kevinanderson86@gmail.com"
SMTP_PASS = "zwyjaptqnoxrrztn"
EMAIL_FROM = "kevinanderson86@gmail.com"
EMAIL_TO = "kevin.anderson@ses.com"


def get_ad_names():
    try:
        response = requests.get(AD_ITEMS_URL, headers=AUTH_HEADER)
        response.raise_for_status()
        data = response.json()
        # Build a mapping from ad ID to ad name
        ad_names = {}
        for ad_item in data.get("data", []):
            ad_id = ad_item.get("id")
            name = ad_item.get("name")
            ad_names[ad_id] = name
        return ad_names
    except Exception as e:
        print(f"Error fetching ad names: {e}")
        return {}


def send_email(subject, body, to_addr=EMAIL_TO):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_FROM
        msg['To'] = to_addr
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(EMAIL_FROM, to_addr, msg.as_string())
    except Exception as e:
        print(f"Error sending email: {e}")


def fetch_and_log(ad_names):
    try:
        response = requests.get(API_URL, headers=AUTH_HEADER)
        response.raise_for_status()
        data = response.json()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Timestamp: {timestamp}")
        sms_lines = [f"Timestamp: {timestamp}\n"]
        for ad_item in data.get("data", []):
            ad_id = ad_item.get("id")
            summary = ad_item.get("summary", {})
            impressions = summary.get("impressions")
            clicks = summary.get("clicks")
            name = ad_names.get(ad_id, f"AD ID: {ad_id}")
            ctr = (clicks / impressions * 100) if impressions else 0
            line = f"{name} Impressions: {impressions} Clicks: {clicks} CTR: {ctr:.2f}%"
            print(line)
            sms_lines.append(line)
        print()
        message = "\n".join(sms_lines)
        send_email("Ad Impressions Report", message)
    except Exception as e:
        print(f"Error fetching data: {e}")


def update_chart_data(timestamp, ad_names, ad_stats):
    DATA_FILE = "ad_data.json"
    try:
        # Load existing data
        try:
            with open(DATA_FILE, "r") as f:
                chart_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            chart_data = {"timestamps": [], "ads": []}
        # Update timestamps
        chart_data["timestamps"].append(timestamp)
        # Update ad stats
        if not chart_data["ads"]:
            for ad_id, stats in ad_stats.items():
                chart_data["ads"].append({
                    "id": ad_id,
                    "name": ad_names.get(ad_id, f"AD ID: {ad_id}"),
                    "impressions": [stats["impressions"]],
                    "clicks": [stats["clicks"]]
                })
        else:
            for ad in chart_data["ads"]:
                ad_id = ad["id"]
                stats = ad_stats.get(ad_id, {"impressions": 0, "clicks": 0})
                ad["impressions"].append(stats["impressions"])
                ad["clicks"].append(stats["clicks"])
        # Save updated data
        with open(DATA_FILE, "w") as f:
            json.dump(chart_data, f)
        print(f"[ad_data.json] Updated at {timestamp}. Total timestamps: {len(chart_data['timestamps'])}")
    except Exception as e:
        print(f"Error updating chart data: {e}")


def main():
    ad_names = get_ad_names()
    prev_stats = {}
    minute_counter = 0
    while True:
        try:
            response = requests.get(API_URL, headers=AUTH_HEADER)
            response.raise_for_status()
            data = response.json()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:00")
            print(f"Timestamp: {timestamp}\n")
            sms_lines = [f"Timestamp: {timestamp}\n"]
            ad_stats = {}
            for ad_item in data.get("data", []):
                ad_id = ad_item.get("id")
                summary = ad_item.get("summary", {})
                impressions = summary.get("impressions")
                clicks = summary.get("clicks")
                name = ad_names.get(ad_id, f"AD ID: {ad_id}")
                ctr = (clicks / impressions * 100) if impressions else 0
                prev = prev_stats.get(ad_id, {"impressions": 0, "clicks": 0})
                diff_impressions = impressions - prev["impressions"]
                diff_clicks = clicks - prev["clicks"]
                line = f"{name}\nImpressions: {impressions} Clicks: {clicks} CTR: {ctr:.2f}%\nDifference: Impressions: {diff_impressions}, Clicks: {diff_clicks}\n"
                print(line)
                sms_lines.append(line)
                prev_stats[ad_id] = {"impressions": impressions, "clicks": clicks}
                ad_stats[ad_id] = {"impressions": impressions, "clicks": clicks}
            print()
            message = "\n".join(sms_lines)
            update_chart_data(timestamp, ad_names, ad_stats)
            minute_counter += 1
            if minute_counter % 5 == 0:
                send_email("Ad Impressions Report", message)
        except Exception as e:
            print(f"Error fetching data: {e}")
        # Sleep until the next minute
        now = datetime.now()
        next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
        sleep_time = (next_minute - now).total_seconds()
        time.sleep(sleep_time)


if __name__ == "__main__":
    main()
