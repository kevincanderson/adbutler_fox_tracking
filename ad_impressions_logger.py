import requests
import time
from datetime import datetime

API_URL = "https://api.adbutler.com/v2/reports?type=ad-item&period=day&preset=today&ad-items=523668188,523668181"
AUTH_HEADER = {
    "Authorization": "Basic 552ad1d70aa376a7e83f42fbfbac9283"
}


def fetch_and_log():
    try:
        response = requests.get(API_URL, headers=AUTH_HEADER)
        response.raise_for_status()
        data = response.json()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Timestamp: {timestamp}")
        # The API returns a list of ad items under 'data', each with 'id' and 'summary' containing 'impressions'
        for ad_item in data.get("data", []):
            ad_id = ad_item.get("id")
            impressions = ad_item.get("summary", {}).get("impressions")
            print(f"AD ID: {ad_id} Impressions: {impressions}")
        print()
    except Exception as e:
        print(f"Error fetching data: {e}")


def main():
    while True:
        fetch_and_log()
        time.sleep(60)


if __name__ == "__main__":
    main()
