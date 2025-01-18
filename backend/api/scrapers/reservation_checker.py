from typing import List, Optional, Dict, Union
from datetime import time, datetime, date, timedelta
from dataclasses import dataclass
from pydantic import BaseModel, field_validator

class StudioValidationError(Exception):
    """バリデーション失敗時に発生する例外"""
    pass

class StudioTimeSlot(BaseModel):
    """スタジオの利用可能時間枠を表すモデル"""
    start_time: time
    end_time: time

    @field_validator('end_time')
    @classmethod
    def validate_time_order(cls, end: time, info) -> time:
        if 'start_time' not in info.data:
            return end
            
        start = info.data['start_time']
        start_minutes = start.hour * 60 + start.minute
        end_minutes = end.hour * 60 + end.minute
        
        # 終了時刻が00:00の場合は24:00として扱う
        if end_minutes == 0:
            end_minutes = 24 * 60
            
        if start_minutes >= end_minutes:
            raise StudioValidationError(
                f"開始時刻({start.strftime('%H:%M')})は"
                f"終了時刻({end.strftime('%H:%M')})より前である必要があります"
            )
        return end

    def to_dict(self) -> Dict[str, str]:
        """時間枠をJSON互換の辞書形式に変換"""
        return {
            "start": self.start_time.strftime("%H:%M"),
            "end": self.end_time.strftime("%H:%M")
        }

class StudioAvailability(BaseModel):
    """スタジオの空き状況を表すモデル"""
    room_name: str
    date: date
    time_slots: List[StudioTimeSlot]
    start_minute: int = 0  # 開始時刻（分）。0, 30, 60などの値を取る
    allows_thirty_minute_slots: bool = False  # 30分単位での予約が可能かどうか

    @field_validator('start_minute')
    @classmethod
    def validate_start_minute(cls, v: int) -> int:
        """開始時刻の妥当性チェック"""
        valid_start_minutes = [0, 30, 60]  # 有効な開始時刻の値
        if v not in valid_start_minutes:
            raise StudioValidationError("開始時刻（分）は0, 30, 60のいずれかである必要があります")
        return v

    def to_dict(self) -> Dict[str, Union[str, List[Dict[str, str]], int, bool]]:
        """空き状況をJSON互換の辞書形式に変換"""
        return {
            "room_name": self.room_name,
            "date": self.date.isoformat(),
            "time_slots": [slot.to_dict() for slot in self.time_slots],
            "start_minute": self.start_minute,
            "allows_thirty_minute_slots": self.allows_thirty_minute_slots
        }

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
        """datetimeオブジェクトからTimeRangeを作成"""
        return cls(dt.time(), dt.time())

    @staticmethod
    def validate_time_order(start: time, end: time) -> None:
        """開始時刻が終了時刻より前であることを検証"""
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
        self.availabilities = availabilities
        # 開始時刻（分）の管理用のマップ
        self._start_minutes: Dict[str, int] = {}
        # 30分単位予約フラグの管理用のマップ
        self._allows_thirty_minute_slots: Dict[str, bool] = {}
        
        # 各部屋の情報を初期化
        for availability in availabilities:
            self._start_minutes[availability.room_name] = availability.start_minute
            # start_minute が 60 の場合は30分単位予約可能
            self._allows_thirty_minute_slots[availability.room_name] = (availability.start_minute == 60)

    def _combine_date_time(self, d: date, t: time) -> datetime:
        """日付と時刻を組み合わせてdatetimeオブジェクトを作成"""
        return datetime.combine(d, t)

    def _to_minutes(self, t: time, is_end_time: bool = False) -> int:
        """時刻を分単位に変換
        
        Args:
            t: 変換する時刻
            is_end_time: 終了時刻として扱うかどうか
        
        Returns:
            int: 分単位の時刻（00:00は通常0分、終了時刻の場合は24:00=1440分として扱う）
        """
        minutes = t.hour * 60 + t.minute
        if minutes == 0 and is_end_time:  # 終了時刻の00:00のみ24:00として扱う
            return 24 * 60
        return minutes

    def find_available_slots(
        self,
        desired_range: TimeRange,
        duration_hours: int
    ) -> List[StudioAvailability]:
        """指定された条件に合う予約可能な時間枠を検索"""
        if duration_hours <= 0:
            raise StudioValidationError("利用時間は正の値である必要があります")
        
        result: List[StudioAvailability] = []
        min_duration_minutes = duration_hours * 60
        
        for availability in self.availabilities:
            # 30分単位での予約が可能な部屋かどうかをチェック
            allows_thirty_minute_slots = self._allows_thirty_minute_slots.get(availability.room_name, False)
            
            filtered_slots = []
            for slot in availability.time_slots:
                slot_duration = (
                    self._to_minutes(slot.end_time, True) -
                    self._to_minutes(slot.start_time, False)
                )
                
                if allows_thirty_minute_slots:
                    # 30分単位予約可能な部屋の場合、30分以上のスロットを許可
                    if slot_duration >= 30:
                        filtered_slots.append(slot)
                else:
                    # 従来通りの時間チェック
                    if slot_duration >= min_duration_minutes:
                        filtered_slots.append(slot)
            
            if filtered_slots:
                # マージされたスロットを作成
                merged_slots = self._merge_filtered_slots(
                    filtered_slots,
                    30 if allows_thirty_minute_slots else min_duration_minutes,
                    availability
                )
                
                # 指定された時間範囲でフィルタリング
                valid_slots = self._filter_slots_in_range(
                    merged_slots,
                    desired_range,
                    30 if allows_thirty_minute_slots else min_duration_minutes,
                    availability
                )
                
                if valid_slots:
                    result.append(StudioAvailability(
                        room_name=availability.room_name,
                        time_slots=valid_slots,
                        date=availability.date,
                        start_minute=availability.start_minute,
                        allows_thirty_minute_slots=allows_thirty_minute_slots
                    ))
        
        return result

    def _merge_filtered_slots(
        self,
        slots: List[StudioTimeSlot],
        min_duration_minutes: int,
        availability: StudioAvailability
    ) -> List[StudioTimeSlot]:
        """フィルタリング済みの時間枠をマージ"""
        if not slots:
            return []

        # 開始時刻でソート
        sorted_slots = sorted(slots, key=lambda x: self._to_minutes(x.start_time, False))
        merged = []
        current = sorted_slots[0]
        
        for next_slot in sorted_slots[1:]:
            current_end = self._to_minutes(current.end_time, True)
            next_start = self._to_minutes(next_slot.start_time, False)
            
            if current_end >= next_start:  # >=に変更して隣接するスロットもマージ
                # 連続しているのでマージ
                current = StudioTimeSlot(
                    start_time=current.start_time,
                    end_time=next_slot.end_time
                )
            else:
                # 現在の時間枠が最小時間以上であれば追加
                slot_duration = (
                    self._to_minutes(current.end_time, True) -
                    self._to_minutes(current.start_time, False)
                )
                if slot_duration >= min_duration_minutes:
                    merged.append(current)
                current = next_slot
        
        # 最後の時間枠を処理
        slot_duration = (
            self._to_minutes(current.end_time, True) -
            self._to_minutes(current.start_time, False)
        )
        if slot_duration >= min_duration_minutes:
            merged.append(current)
        
        return merged

    def _filter_slots_in_range(
        self,
        slots: List[StudioTimeSlot],
        desired_range: TimeRange,
        min_duration_minutes: int,
        availability: StudioAvailability
    ) -> List[StudioTimeSlot]:
        """指定された時間範囲内の時間枠をフィルタリング"""
        filtered = []
        range_start = self._to_minutes(desired_range.start, False)  # 開始時刻
        range_end = self._to_minutes(desired_range.end, True)  # 終了時刻
        
        for slot in slots:
            slot_start = self._to_minutes(slot.start_time, False)  # 開始時刻
            slot_end = self._to_minutes(slot.end_time, True)  # 終了時刻
            
            if slot_start < range_end and slot_end > range_start:
                new_start_minutes = max(slot_start, range_start)
                new_end_minutes = min(slot_end, range_end)
                
                # 時間枠の長さが最小時間以上であることを確認
                if new_end_minutes - new_start_minutes >= min_duration_minutes:
                    # minutes を time オブジェクトに変換
                    new_start = time(
                        (new_start_minutes % 1440) // 60,
                        new_start_minutes % 60
                    )
                    
                    # 終了時刻の処理
                    if new_end_minutes == 24 * 60:
                        new_end = time(0, 0)
                    else:
                        new_end = time(
                            (new_end_minutes % 1440) // 60,
                            new_end_minutes % 60
                        )
                    
                    # 開始時刻の分だけ終了時刻を調整
                    if availability.start_minute > 0:
                        if new_end_minutes == 24 * 60:
                            new_end = time(23, 60 - availability.start_minute)
                        else:
                            end_minutes = new_end_minutes - availability.start_minute
                            new_end = time(
                                (end_minutes % 1440) // 60,
                                end_minutes % 60
                            )
                    
                    filtered.append(StudioTimeSlot(
                        start_time=new_start,
                        end_time=new_end
                    ))
        
        return filtered