import requests
import time
from datetime import datetime
import json

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
        print("Raw API response:")
        print(json.dumps(data, indent=2))
        print()
    except Exception as e:
        print(f"Error fetching data: {e}")


def main():
    while True:
        fetch_and_log()
        time.sleep(60)


if __name__ == "__main__":
    main()
