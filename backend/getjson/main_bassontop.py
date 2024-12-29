from scraper_bassontop import StudioScraper
from analyzer_bassontop import StudioAnalyzer

def main():
    # 設定値
    studio_id = 673
    booking_date = "2024-12-30"
    usage_hours = 2  # 時間単位
    search_start_time = "09:00"
    search_end_time = "23:00"
    
    try:
        # スケジュール取得
        scraper = StudioScraper(studio_id, search_start_time, search_end_time)
        print(f"{booking_date}の予約状況を取得中...")
        schedule_data = scraper.fetch_schedule(booking_date)
        
        # # JSONファイルとして保存
        # json_filename = f"予約状況_{booking_date}.json"
        # json_file = scraper.save_schedule(schedule_data, json_filename)
        # print(f"予約データを {json_file} に保存しました")
        
        # スケジュール分析
        analyzer = StudioAnalyzer()
        print(f"\n利用可能な部屋を検索中...")
        print(f"検索条件: {usage_hours}時間, {search_start_time}～{search_end_time}")
        
        available_rooms = analyzer.analyze_schedule(
            data=schedule_data,
            date_str=booking_date,
            duration_hours=usage_hours,
            range_start=search_start_time,
            range_end=search_end_time
        )
                
        # 結果表示
        if not available_rooms:
            print("\n条件に合う利用可能な部屋はありませんでした。")
        else:
            print("\n利用可能な部屋と時間帯:")
            for room_id, time_ranges in available_rooms:
                print(f"\n部屋番号: {room_id}")
                for time_range in time_ranges:
                    print(f"  {time_range}")
                    
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")

if __name__ == "__main__":
    main()