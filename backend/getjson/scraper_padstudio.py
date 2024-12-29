import os
import requests
from datetime import datetime

class StudioReserveScraper:
    def __init__(self, save_dir="./json"):
        self.base_url = "https://www.reserve1.jp/studio/member"
        self.save_dir = save_dir
        self.session = requests.Session()
        os.makedirs(save_dir, exist_ok=True)

    def fetch_login_page(self):
        """ログインページを取得"""
        url = f"{self.base_url}/VisitorLogin.php"
        params = {
            "lc": "olsccsvld",
            "mn": "3",
            "gr": "1"
        }
        response = self.session.get(url, params=params)
        
        if response.status_code != 200 or not response.text.strip():
            raise Exception("Failed to fetch login page")
        
        return response.text

    def fetch_schedule(self, date_str, office_id="1480320"):
        """指定された日付の予約スケジュールを取得"""
        url = f"{self.base_url}/member_select.php"
        
        # 年月を取得 (YYYYMM形式)
        ym = date_str[:7].replace("-", "")
        
        data = {
            "grand": "1",
            "Ym_select": ym,
            "office": office_id,
            "mngfg": "4",
            "rdate": date_str,
            "member_select": "3",
            "month_btn": "",
            "day_btn": date_str
        }

        response = self.session.post(url, data=data)
        
        if response.status_code != 200 or not response.text.strip():
            raise Exception("Failed to fetch schedule data")

        return response.text

def main():
    try:
        # スクレイパーのインスタンスを作成
        scraper = StudioReserveScraper()
        
        # ログインページを取得
        print("ログインページを取得中...")
        scraper.fetch_login_page()
        
        # スケジュールを取得
        print("予約スケジュールを取得中...")
        schedule_data = scraper.fetch_schedule("2025-01-07")
        
        return schedule_data
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()