from typing import List, Dict
from datetime import datetime
from scraper_base import StudioAvailability, StudioTimeSlot

class AvailabilityChecker:
    def __init__(self, schedule_data: List[Dict]):
        """
        予約チェッカーの初期化
        
        Args:
            schedule_data: スタジオごとの予約可能時間が含まれるJSONデータ
        """
        self.availabilities = self._convert_to_availabilities(schedule_data)

    def _parse_time(self, time_str: str) -> datetime:
        """時刻文字列をdatetimeオブジェクトに変換"""
        return datetime.strptime(time_str, "%H:%M")

    def _format_time(self, dt: datetime) -> str:
        """datetimeオブジェクトを時刻文字列に変換"""
        return dt.strftime("%H:%M")

    def _convert_to_availabilities(self, schedule_data: List[Dict]) -> List[StudioAvailability]:
        """
        スケジュールデータをStudioAvailabilityオブジェクトに変換
        
        Args:
            schedule_data: 元のスケジュールデータ
            
        Returns:
            List[StudioAvailability]: 変換後のデータ
        """
        availabilities = []
        current_date = datetime.now().strftime("%Y-%m-%d")  # 現在の日付をデフォルトとして使用
        
        for studio in schedule_data:
            time_slots = [
                StudioTimeSlot(
                    start_time=slot["start"],
                    end_time=slot["end"]
                )
                for slot in studio["available_times"]
            ]
            
            availability = StudioAvailability(
                room_name=studio["name"],
                time_slots=time_slots,
                date=current_date
            )
            availabilities.append(availability)
            
        return availabilities

    def _merge_time_slots(self, slots: List[StudioTimeSlot]) -> List[StudioTimeSlot]:
        """時間枠をマージして最大の範囲を取得"""
        if not slots:
            return []

        # 時間枠を開始時刻でソート
        sorted_slots = sorted(slots, key=lambda x: self._parse_time(x.start_time))
        merged = []
        current_slot = StudioTimeSlot(
            start_time=sorted_slots[0].start_time,
            end_time=sorted_slots[0].end_time
        )

        for slot in sorted_slots[1:]:
            current_end = self._parse_time(current_slot.end_time)
            next_start = self._parse_time(slot.start_time)
            next_end = self._parse_time(slot.end_time)

            if current_end >= next_start:
                # スロットが重なっているか連続している場合、マージ
                if next_end > self._parse_time(current_slot.end_time):
                    current_slot = StudioTimeSlot(
                        start_time=current_slot.start_time,
                        end_time=slot.end_time
                    )
            else:
                # 連続していない場合、新しいスロットを開始
                merged.append(current_slot)
                current_slot = StudioTimeSlot(
                    start_time=slot.start_time,
                    end_time=slot.end_time
                )

        merged.append(current_slot)
        return merged

    def find_available_slots(self, desired_start: str, desired_end: str, duration_hours: int) -> List[StudioAvailability]:
        """
        指定された条件に合う予約可能な時間枠を検索
        
        Args:
            desired_start: 希望開始時刻 (HH:MM形式)
            desired_end: 希望終了時刻 (HH:MM形式)
            duration_hours: 利用希望時間（時間単位）
            
        Returns:
            List[StudioAvailability]: 予約可能な時間枠のリスト
        """
        start_time = self._parse_time(desired_start)
        end_time = self._parse_time(desired_end)
        
        result = []
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        for availability in self.availabilities:
            # 希望時間帯内の時間枠をフィルタリング
            filtered_slots = []
            for slot in availability.time_slots:
                slot_start = self._parse_time(slot.start_time)
                slot_end = self._parse_time(slot.end_time)
                
                if slot_start >= start_time and slot_end <= end_time:
                    filtered_slots.append(slot)

            # 時間枠をマージ
            merged_slots = self._merge_time_slots(filtered_slots)
            
            # 利用希望時間以上の時間枠のみを抽出
            valid_slots = []
            for slot in merged_slots:
                slot_duration = (
                    self._parse_time(slot.end_time) - 
                    self._parse_time(slot.start_time)
                ).total_seconds() / 3600  # 時間単位に変換
                
                if slot_duration >= duration_hours:
                    valid_slots.append(slot)
            
            if valid_slots:
                result.append(StudioAvailability(
                    room_name=availability.room_name,
                    time_slots=valid_slots,
                    date=current_date
                ))
        
        return result

def main():
    # サンプルデータ
    schedule_data = [
        {
            "name": "Astudio",
            "available_times": [
                {"start": "20:00", "end": "21:00"},
                {"start": "21:00", "end": "22:00"}
            ]
        },
        {
            "name": "Bstudio",
            "available_times": [
                {"start": "14:00", "end": "15:00"},
                {"start": "15:00", "end": "16:00"},
                {"start": "16:00", "end": "17:00"},
                {"start": "17:00", "end": "18:00"},
                {"start": "20:00", "end": "21:00"},
                {"start": "21:00", "end": "22:00"}
            ]
        }
    ]
    
    checker = AvailabilityChecker(schedule_data)
    result = checker.find_available_slots("14:00", "22:00", 2)
    
    # 結果の表示
    for availability in result:
        print(f"\n{availability.room_name}の予約可能時間:")
        for slot in availability.time_slots:
            print(f"  {slot.start_time} - {slot.end_time}")

if __name__ == "__main__":
    main()