from analyzer_padstudio import analyze_studio_schedule
from scraper_padstudio import StudioReserveScraper

def main():
    booking_date = "2025-01-08"
    usage_hours = 2  # 時間単位
    search_start_time = "09:00"
    search_end_time = "23:00" 
        
    try:
        # スケジュール取得
        scraper = StudioReserveScraper()
        print(f"{booking_date}の予約状況を取得中...")
        html_content = scraper.fetch_schedule(booking_date)

        print("\n=== 2時間枠での空き状況（12:00-22:00） ===")
        # 2時間枠での検索
        available_slots = analyze_studio_schedule(
            html_content=html_content,
            duration_hours=usage_hours,
            range_start=search_start_time,
            range_end=search_end_time
        )
        
        if not available_slots:
            print("\n条件に合う利用可能な部屋はありませんでした。")
        else:
            for studio, times in available_slots:
                print(f"{studio}:")
                for time_range in times:
                    print(f"  {time_range}")
                    
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")

if __name__ == "__main__":
    main()

