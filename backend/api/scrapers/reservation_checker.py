from typing import List, Optional
from datetime import time, datetime, date, timedelta
from dataclasses import dataclass
from scraper_base import (
    StudioTimeSlot,
    StudioAvailability,
    StudioValidationError
)

@dataclass
class TimeRange:
    """時間範囲を表すデータクラス"""
    start: time
    end: time

    def __post_init__(self) -> None:
        """初期化後の検証"""
        self.validate_time_order(self.start, self.end)

    @classmethod
    def from_datetime(cls, dt: datetime) -> 'TimeRange':
        """datetimeオブジェクトからTimeRangeを作成
        
        Args:
            dt: 変換元のdatetimeオブジェクト
            
        Returns:
            TimeRange: 作成された時間範囲オブジェクト
        """
        return cls(dt.time(), dt.time())

    @staticmethod
    def validate_time_order(start: time, end: time) -> None:
        """開始時刻が終了時刻より前であることを検証
        
        Args:
            start: 開始時刻
            end: 終了時刻
            
        Raises:
            StudioValidationError: 時刻の順序が不正な場合
        """
        start_minutes = start.hour * 60 + start.minute
        end_minutes = end.hour * 60 + end.minute
        
        if end_minutes == 0:
            end_minutes = 24 * 60
            
        if start_minutes >= end_minutes:
            raise StudioValidationError(
                f"開始時刻({start.strftime('%H:%M')})は"
                f"終了時刻({end.strftime('%H:%M')})より前である必要があります"
            )

class AvailabilityChecker:
    """予約可能時間をチェックするクラス"""

    def __init__(self, availabilities: List[StudioAvailability]):
        """予約チェッカーの初期化
        
        Args:
            availabilities: StudioAvailabilityオブジェクトのリスト
        """
        self.availabilities = availabilities

    def _combine_date_time(self, d: date, t: time) -> datetime:
        """日付と時刻を組み合わせてdatetimeオブジェクトを作成"""
        return datetime.combine(d, t)

    def _to_minutes(self, t: time) -> int:
        """時刻を分単位に変換"""
        return t.hour * 60 + t.minute

    def find_available_slots(
        self,
        desired_range: TimeRange,
        duration_hours: int
    ) -> List[StudioAvailability]:
        """指定された条件に合う予約可能な時間枠を検索"""
        if duration_hours <= 0:
            raise StudioValidationError("利用時間は正の値である必要があります")
        
        result: List[StudioAvailability] = []
        
        for availability in self.availabilities:
            merged_slots = self._merge_time_slots(availability.time_slots)
            filtered_slots = self._filter_slots_in_range(
                merged_slots,
                desired_range
            )
            valid_slots = self._filter_slots_by_duration(
                filtered_slots,
                duration_hours
            )
            
            if valid_slots:
                result.append(StudioAvailability(
                    room_name=availability.room_name,
                    time_slots=valid_slots,
                    date=availability.date
                ))
        
        return result

    def _merge_time_slots(self, slots: List[StudioTimeSlot]) -> List[StudioTimeSlot]:
        """時間枠をマージして最大の範囲を取得"""
        if not slots:
            return []

        sorted_slots = sorted(slots, key=lambda x: self._to_minutes(x.start_time))
        merged: List[StudioTimeSlot] = []
        current_slot = sorted_slots[0]

        for slot in sorted_slots[1:]:
            current_end = self._to_minutes(current_slot.end_time)
            next_start = self._to_minutes(slot.start_time)
            next_end = self._to_minutes(slot.end_time)
            
            if current_end == next_start:
                if next_end > current_end or (next_end == 0 and current_end != 24 * 60):
                    current_slot = StudioTimeSlot(
                        start_time=current_slot.start_time,
                        end_time=slot.end_time
                    )
            else:
                merged.append(current_slot)
                current_slot = slot

        merged.append(current_slot)
        return merged

    def _filter_slots_in_range(
        self,
        slots: List[StudioTimeSlot],
        desired_range: TimeRange
    ) -> List[StudioTimeSlot]:
        """指定された時間範囲内の時間枠をフィルタリング"""
        filtered: List[StudioTimeSlot] = []
        
        for slot in slots:
            slot_start = self._to_minutes(slot.start_time)
            slot_end = self._to_minutes(slot.end_time)
            if slot_end == 0:
                slot_end = 24 * 60
            
            range_start = self._to_minutes(desired_range.start)
            range_end = self._to_minutes(desired_range.end)
            if range_end == 0:
                range_end = 24 * 60
                
            if slot_start < range_end and slot_end > range_start:
                new_start_minutes = max(slot_start, range_start)
                new_end_minutes = min(slot_end, range_end)
                
                new_start = time(new_start_minutes // 60, new_start_minutes % 60)
                new_end = time(0, 0) if new_end_minutes == 24 * 60 else time(new_end_minutes // 60, new_end_minutes % 60)
                
                filtered.append(StudioTimeSlot(
                    start_time=new_start,
                    end_time=new_end
                ))
                
        return filtered

    def _filter_slots_by_duration(
        self,
        slots: List[StudioTimeSlot],
        duration_hours: int
    ) -> List[StudioTimeSlot]:
        """指定された時間以上の長さを持つ時間枠をフィルタリング"""
        valid: List[StudioTimeSlot] = []
        min_duration_minutes = duration_hours * 60
        
        for slot in slots:
            start_minutes = self._to_minutes(slot.start_time)
            end_minutes = self._to_minutes(slot.end_time)
            if end_minutes == 0:
                end_minutes = 24 * 60
                
            duration = end_minutes - start_minutes
            
            if duration >= min_duration_minutes:
                valid.append(slot)
                    
        return valid

def main():
    """使用例：実際のスクレイパーを使用してスタジオの空き状況を確認"""
    from scraper_studiol import StudioOLScraper
    from scraper_padstudio import PadStudioScraper
    from datetime import date, time
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    try:
        studiol_scraper = StudioOLScraper()
        padstudio_scraper = PadStudioScraper()
        shop_id = "673"
        
        studiol_scraper.establish_connection(shop_id=shop_id)
        padstudio_scraper.establish_connection()
        
        target_date = date(2025, 1, 5)
        
        studiol_availabilities = studiol_scraper.fetch_available_times(target_date)
        padstudio_availabilities = padstudio_scraper.fetch_available_times(target_date)
        
        studiol_checker = AvailabilityChecker(studiol_availabilities)
        padstudio_checker = AvailabilityChecker(padstudio_availabilities)
        
        desired_range = TimeRange(
            start=time(hour=16),
            end=time(hour=22)
        )
        duration_hours = 2
        
        studiol_result = studiol_checker.find_available_slots(desired_range, duration_hours)
        padstudio_result = padstudio_checker.find_available_slots(desired_range, duration_hours)
        
        print("\n=== Studio-OL 検索結果 ===")
        if studiol_result:
            for availability in studiol_result:
                print(f"\nスタジオ: {availability.room_name}")
                print("条件に合う予約可能時間:")
                for slot in availability.time_slots:
                    start_minutes = studiol_checker._to_minutes(slot.start_time)
                    end_minutes = studiol_checker._to_minutes(slot.end_time)
                    if end_minutes == 0:
                        end_minutes = 24 * 60
                    duration_hours = (end_minutes - start_minutes) / 60
                    print(f"  {slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')} (計{duration_hours:.1f}時間)")
        else:
            print("条件に合う予約可能時間は見つかりませんでした。")
        
        print("\n=== PAD Studio 検索結果 ===")
        if padstudio_result:
            for availability in padstudio_result:
                print(f"\nスタジオ: {availability.room_name}")
                print("条件に合う予約可能時間:")
                for slot in availability.time_slots:
                    start_minutes = padstudio_checker._to_minutes(slot.start_time)
                    end_minutes = padstudio_checker._to_minutes(slot.end_time)
                    if end_minutes == 0:
                        end_minutes = 24 * 60
                    duration_hours = (end_minutes - start_minutes) / 60
                    print(f"  {slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')} (計{duration_hours:.1f}時間)")
        else:
            print("条件に合う予約可能時間は見つかりませんでした。")
                
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()