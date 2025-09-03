from flask import Flask, render_template, jsonify, request
import json
import os
import threading
import time
from datetime import datetime, timedelta
import requests

app = Flask(__name__)

DATA_FILE = "ad_data.json"
API_URL = "https://api.adbutler.com/v2/reports?type=ad-item&period=day&preset=today&ad-items=523668188,523668181"
AD_ITEMS_URL = "https://api.adbutler.com/v2/ad-items?limit=100&id=523668188,523668181"
AUTH_HEADER = {
    "Authorization": "Basic 552ad1d70aa376a7e83f42fbfbac9283"
}

logger_thread = None
logger_running = False


def get_ad_names():
    try:
        response = requests.get(AD_ITEMS_URL, headers=AUTH_HEADER)
        response.raise_for_status()
        data = response.json()
        ad_names = {}
        for ad_item in data.get("data", []):
            ad_id = ad_item.get("id")
            name = ad_item.get("name")
            ad_names[ad_id] = name
        return ad_names
    except Exception as e:
        print(f"Error fetching ad names: {e}")
        return {}


def update_chart_data(timestamp, ad_names, ad_stats):
    try:
        try:
            with open(DATA_FILE, "r") as f:
                chart_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            chart_data = {"timestamps": [], "ads": []}
        chart_data["timestamps"].append(timestamp)
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
        with open(DATA_FILE, "w") as f:
            json.dump(chart_data, f)
        print(f"[ad_data.json] Updated at {timestamp}. Total timestamps: {len(chart_data['timestamps'])}")
    except Exception as e:
        print(f"Error updating chart data: {e}")


def logger():
    global logger_running
    ad_names = get_ad_names()
    prev_stats = {}
    while logger_running:
        try:
            response = requests.get(API_URL, headers=AUTH_HEADER)
            response.raise_for_status()
            data = response.json()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:00")
            ad_stats = {}
            for ad_item in data.get("data", []):
                ad_id = ad_item.get("id")
                summary = ad_item.get("summary", {})
                impressions = summary.get("impressions")
                clicks = summary.get("clicks")
                ad_stats[ad_id] = {"impressions": impressions, "clicks": clicks}
                prev_stats[ad_id] = {"impressions": impressions, "clicks": clicks}
            update_chart_data(timestamp, ad_names, ad_stats)
        except Exception as e:
            print(f"Error fetching data: {e}")
        now = datetime.now()
        next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
        sleep_time = (next_minute - now).total_seconds()
        time.sleep(sleep_time)

@app.route("/")
def index():
    global logger_thread, logger_running
    if not logger_running:
        logger_running = True
        logger_thread = threading.Thread(target=logger, daemon=True)
        logger_thread.start()
    return render_template("chart.html")

@app.route("/data")
def data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {}
    return jsonify(data)

@app.route("/stop_logger", methods=["POST"])
def stop_logger():
    global logger_running
    logger_running = False
    return "Logger stopped"

if __name__ == "__main__":
    app.run(debug=True)
