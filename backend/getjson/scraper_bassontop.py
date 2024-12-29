import os
import re
import requests
import json
from datetime import datetime

class StudioScraper:
    def __init__(self, shop_id, search_start_time, search_end_time ,save_dir="./json"):
        self.shop_id = shop_id
        self.save_dir = save_dir
        self.session = requests.Session()
        os.makedirs(save_dir, exist_ok=True)

    def fetch_schedule(self, date_str):
        """指定された日付の予約スケジュールを取得"""
        # HTMLを取得してトークンを抽出
        response = self.session.get(f"https://studi-ol.com/shop/{self.shop_id}")
        if response.status_code != 200:
            raise Exception("Failed to fetch HTML")

        match = re.search(r'name="_token" value="([^"]+)"', response.text)
        if not match:
            raise Exception("Failed to extract token")
        
        token = match.group(1)

        # スケジュールデータを取得
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        data = {
            "_token": token,
            "shop_id": str(self.shop_id),
            "start": f"{date_str} 07:00:00",
            "end": f"{date_str} 23:00:00",
        }

        response = self.session.post(
            "https://studi-ol.com/get_schedule_shop",
            headers=headers,
            data=data
        )
        
        if response.status_code != 200:
            raise Exception("Failed to fetch schedule data")

        return json.loads(response.text)

    def save_schedule(self, data, filename):
        """スケジュールデータをJSONファイルとして保存"""
        filepath = os.path.join(self.save_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return filepath