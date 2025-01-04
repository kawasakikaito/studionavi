from typing import List
from datetime import date, datetime, time, timedelta
from dataclasses import dataclass
from scraper_base import StudioTimeSlot, StudioAvailability

@dataclass
class TimeRange:
    """時間範囲を表すデータクラス"""
    start: time
    end: time

    @classmethod
    def from_datetime(cls, dt: datetime) -> 'TimeRange':
        """datetimeオブジェクトからTimeRangeを作成"""
        return cls(dt.time(), dt.time())

    @classmethod
    def validate_time_order(cls, start: time, end: time) -> None:
        """開始時刻が終了時刻より前であることを検証"""
        # 時刻を分単位に変換
        start_minutes = start.hour * 60 + start.minute
        end_minutes = end.hour * 60 + end.minute
        
        # 終了時刻が00:00の場合は24:00として扱う
        if end_minutes == 0:
            end_minutes = 24 * 60
            
        if start_minutes >= end_minutes:
            raise ValueError(
                f"開始時刻({start.strftime('%H:%M')})は"
                f"終了時刻({end.strftime('%H:%M')})より前である必要があります"
            )

class AvailabilityChecker:
    def __init__(self, availabilities: List[StudioAvailability]):
        """
        予約チェッカーの初期化
        
        Args:
            availabilities: StudioAvailabilityオブジェクトのリスト
        """
        self.availabilities = availabilities

    def _combine_date_time(self, d: date, t: time) -> datetime:
        """日付と時刻を組み合わせてdatetimeオブジェクトを作成"""
        return datetime.combine(d, t)

    def _merge_time_slots(self, slots: List[StudioTimeSlot]) -> List[StudioTimeSlot]:
        """時間枠をマージして最大の範囲を取得"""
        if not slots:
            return []

        # 時間枠を開始時刻でソート
        sorted_slots = sorted(slots, key=lambda x: x.start_time)
        merged = []
        current_slot = sorted_slots[0]

        for slot in sorted_slots[1:]:
            # datetimeオブジェクトを使用して比較
            current_end = self._combine_date_time(date.today(), current_slot.end_time)
            next_start = self._combine_date_time(date.today(), slot.start_time)
            next_end = self._combine_date_time(date.today(), slot.end_time)

            if current_end >= next_start:
                # スロットが重なっているか連続している場合、マージ
                if next_end > self._combine_date_time(date.today(), current_slot.end_time):
                    current_slot = StudioTimeSlot(
                        start_time=current_slot.start_time,
                        end_time=slot.end_time
                    )
            else:
                # 連続していない場合、新しいスロットを開始
                merged.append(current_slot)
                current_slot = slot

        merged.append(current_slot)
        return merged

    def find_available_slots(self, desired_range: TimeRange, duration_hours: int) -> List[StudioAvailability]:
        """
        指定された条件に合う予約可能な時間枠を検索
        
        Args:
            desired_range: 希望する時間範囲
            duration_hours: 利用希望時間（時間単位）
            
        Returns:
            List[StudioAvailability]: 予約可能な時間枠のリスト
            
        Raises:
            ValueError: 無効な時間範囲が指定された場合
        """
        # 時間範囲の妥当性を検証
        TimeRange.validate_time_order(desired_range.start, desired_range.end)
        
        # 検索用のdatetimeオブジェクトを作成
        today = date.today()  # 比較用の基準日
        start_dt = self._combine_date_time(today, desired_range.start)
        end_dt = self._combine_date_time(today, desired_range.end)
        
        result = []
        
        for availability in self.availabilities:
            # 希望時間帯内の時間枠をフィルタリング
            filtered_slots = []
            for slot in availability.time_slots:
                slot_start_dt = self._combine_date_time(today, slot.start_time)
                slot_end_dt = self._combine_date_time(today, slot.end_time)
                
                if slot_start_dt >= start_dt and slot_end_dt <= end_dt:
                    filtered_slots.append(slot)

            # 時間枠をマージ
            merged_slots = self._merge_time_slots(filtered_slots)
            
            # 利用希望時間以上の時間枠のみを抽出
            valid_slots = []
            for slot in merged_slots:
                slot_start_dt = self._combine_date_time(today, slot.start_time)
                slot_end_dt = self._combine_date_time(today, slot.end_time)
                slot_duration = (slot_end_dt - slot_start_dt).total_seconds() / 3600
                
                if slot_duration >= duration_hours:
                    valid_slots.append(slot)
            
            if valid_slots:
                result.append(StudioAvailability(
                    room_name=availability.room_name,
                    time_slots=valid_slots,
                    date=availability.date
                ))
        
        return result


def main():
    """使用例"""
    from scraper_studiol import StudioOLScraper
    
    # スクレイパーの初期化と接続
    scraper = StudioOLScraper()
    scraper.establish_connection(shop_id="673")
    
    # テスト用の日付
    target_date = date(2025, 1, 4)
    
    # 空き状況の取得
    availabilities = scraper.fetch_available_times(target_date)
    
    # 空き状況チェッカーの初期化
    checker = AvailabilityChecker(availabilities)
    
    # 希望時間範囲の作成
    desired_range = TimeRange(
        start=time(hour=14),  # 14:00
        end=time(hour=22)     # 22:00
    )
    
    # 条件に合う空き状況を検索（2時間以上の枠を検索）
    result = checker.find_available_slots(desired_range, 2)
    
    # 結果の表示
    print("希望条件に合う空き状況:")
    for availability in result:
        print(f"\n{availability.room_name}の予約可能時間:")
        for slot in availability.time_slots:
            print(f"  {slot.start_time} - {slot.end_time}")


if __name__ == "__main__":
    main()