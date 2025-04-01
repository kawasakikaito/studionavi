#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django
import logging
from datetime import date

# Djangoの設定を読み込む
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# ロギングの設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)

# スクレイパーのインポート
from api.scrapers.scraper_padstudio import PadStudioScraper
from api.scrapers.scraper_base import StudioScraperError

def test_padstudio_scraper():
    """PADスタジオスクレイパーのテスト"""
    print("PADスタジオスクレイパーのテストを開始します")
    
    # スクレイパーのインスタンス化
    scraper = PadStudioScraper()
    
    try:
        # 接続の確立
        print("接続を確立しています...")
        scraper.establish_connection()
        
        # 本日の空き状況を取得
        today = date.today()
        print(f"{today}の空き状況を取得しています...")
        availabilities = scraper.fetch_available_times(today)
        
        # 結果の表示
        print(f"取得結果: {len(availabilities)}件の空き状況")
        for avail in availabilities:
            print(f"部屋名: {avail.room_name}")
            print(f"日付: {avail.date}")
            print(f"時間枠: {len(avail.time_slots)}件")
            for slot in avail.time_slots:
                print(f"  {slot.start_time} - {slot.end_time}")
            print("---")
        
        print("テストが正常に完了しました")
        
    except StudioScraperError as e:
        print(f"スクレイパーエラー: {e}")
    except Exception as e:
        print(f"予期せぬエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_padstudio_scraper()
