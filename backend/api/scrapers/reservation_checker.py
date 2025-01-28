from typing import List, Optional, Dict, Union, Set
from datetime import time, datetime, date, timedelta
from dataclasses import dataclass
from pydantic import BaseModel, field_validator
from config.logging_config import setup_logger

logger = setup_logger(__name__)

class StudioValidationError(Exception):
    """バリデーション失敗時に発生する例外"""
    pass

class StudioTimeSlot(BaseModel):
    """スタジオの利用可能時間枠を表すモデル"""
    start_time: time
    end_time: time
    
    class Config:
        frozen = True  # イミュータブルにする
        allow_mutation = False  # 変更を禁止する

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
    start_minutes: List[int] = [0]  # 複数の開始時刻を保持
    allows_thirty_minute_slots: bool = False

    @field_validator('start_minutes')
    @classmethod
    def validate_start_minutes(cls, v: List[int]) -> List[int]:
        """開始時刻の妥当性チェック"""
        # 15分単位の開始時刻を許可
        valid_minutes = {0, 15, 30, 45}
        invalid_minutes = set(v) - valid_minutes
        if invalid_minutes:
            raise StudioValidationError(
                f"無効な開始時刻（分）が含まれています: {invalid_minutes}\n"
                "開始時刻（分）は0、15、30、45のいずれかである必要があります"
            )
        return sorted(list(set(v)))  # 重複を削除してソート

    def to_dict(self) -> Dict[str, Union[str, List[Dict[str, str]], List[int], bool]]:
        """空き状況をJSON互換の辞書形式に変換"""
        return {
            "room_name": self.room_name,
            "date": self.date.isoformat(),
            "time_slots": [slot.to_dict() for slot in self.time_slots],
            "start_minutes": self.start_minutes,
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
        
        # 終了時刻が00:00の場合は24:00として扱う
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
        # 開始時刻（分）の管理用のマップ（複数値対応）
        self._start_minutes_map: Dict[str, List[int]] = {}
        # 30分単位予約フラグの管理用のマップ
        self._allows_thirty_minute_slots_map: Dict[str, bool] = {}
        
        # 各部屋の情報を初期化
        for availability in availabilities:
            self._start_minutes_map[availability.room_name] = availability.start_minutes
            self._allows_thirty_minute_slots_map[availability.room_name] = availability.allows_thirty_minute_slots

    def _combine_date_time(self, d: date, t: time) -> datetime:
        """日付と時刻を組み合わせてdatetimeオブジェクトを作成"""
        return datetime.combine(d, t)

    def _to_minutes(self, t: time, is_end_time: bool = False) -> int:
        """時刻を分単位に変換"""
        minutes = t.hour * 60 + t.minute
        if minutes == 0 and is_end_time:  # 終了時刻の00:00のみ24:00として扱う
            return 24 * 60
        return minutes

    def filter_slots_in_range(
        self,
        slots: List[StudioTimeSlot],
        desired_range: TimeRange,
        min_duration_minutes: int,
        start_minute: int
    ) -> Set[StudioTimeSlot]:
        """指定された時間範囲内の時間枠をフィルタリング"""
        filtered = set()
        logger.debug("=== 時間枠フィルタリング詳細 ===")
        logger.debug(f"入力された時間枠数: {len(slots)}")
        logger.debug(f"最小予約時間: {min_duration_minutes}分")
        logger.debug(f"予約開始可能時刻（分）: {start_minute}")
        
        # 時間変換前の値をログ
        logger.debug(f"処理前の時間範囲: {desired_range.start.strftime('%H:%M')}-{desired_range.end.strftime('%H:%M')}")
        range_start = self._to_minutes(desired_range.start, False)
        range_end = self._to_minutes(desired_range.end, True)
        logger.debug(f"分に変換後の時間範囲: {range_start}分-{range_end}分")
        
        for slot in slots:
            logger.debug(f"\n--- 時間枠処理開始 ---")
            logger.debug(f"処理中の時間枠: {slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')}")
            slot_start = self._to_minutes(slot.start_time, False)
            slot_end = self._to_minutes(slot.end_time, True)
            logger.debug(f"分に変換後の時間枠: {slot_start}分-{slot_end}分")
            
            # スタジオの利用可能時間と希望時間範囲が重なっているかチェック
            if slot_start >= range_end or slot_end <= range_start:
                logger.debug("→ 希望時間範囲外のためスキップ")
                continue
                
            # 実際の開始時刻を計算
            actual_start = max(slot_start, range_start)
            logger.debug(f"仮の開始時刻: {actual_start}分 ({actual_start//60}:{actual_start%60:02d})")
            
            # start_minuteを考慮して開始時刻を調整
            current_hour = (actual_start // 60)
            adjusted_start = (current_hour * 60) + start_minute
            logger.debug(f"開始時刻の調整過程:")
            logger.debug(f"  現在の時間: {current_hour}時")
            logger.debug(f"  調整前の開始時刻: {adjusted_start}分 ({adjusted_start//60}:{adjusted_start%60:02d})")
            
            if adjusted_start < actual_start:
                adjusted_start += 60  # 次の時間の開始時刻に調整
                logger.debug(f"  開始時刻を次の時間に調整: {adjusted_start}分 ({adjusted_start//60}:{adjusted_start%60:02d})")
                
            # 終了時刻の計算
            actual_end = min(slot_end, range_end)
            logger.debug(f"終了時刻: {actual_end}分 ({actual_end//60}:{actual_end%60:02d})")
            
            # 予約可能時間が最小時間以上あるかチェック
            available_duration = actual_end - adjusted_start
            logger.debug(f"利用可能時間: {available_duration}分")
            
            # 30分単位での予約が可能な場合、開始時刻の調整を許容
            if available_duration >= min_duration_minutes and (
                adjusted_start % 60 == start_minute  # 開始時刻が指定された分に合致
            ):
                # minutes を time オブジェクトに変換
                new_start = time(
                    (adjusted_start % 1440) // 60,
                    adjusted_start % 60
                )
                
                if actual_end == 24 * 60:
                    new_end = time(0, 0)
                else:
                    new_end = time(
                        (actual_end % 1440) // 60,
                        actual_end % 60
                    )
                
                new_slot = StudioTimeSlot(
                    start_time=new_start,
                    end_time=new_end
                )
                filtered.add(new_slot)
                logger.debug(f"→ 追加された時間枠: {new_start.strftime('%H:%M')}-{new_end.strftime('%H:%M')}")
            else:
                logger.debug(f"→ 時間枠が最小予約時間({min_duration_minutes}分)より短いためスキップ")
        
        logger.debug(f"\n=== フィルタリング結果 ===")
        logger.debug(f"フィルタリング後の時間枠数: {len(filtered)}")
        for result_slot in filtered:
            logger.debug(f"  {result_slot.start_time.strftime('%H:%M')}-{result_slot.end_time.strftime('%H:%M')}")
        
        return filtered

    def find_available_slots(
        self,
        desired_range: TimeRange,
        duration_hours: float
    ) -> List[StudioAvailability]:
        """指定された条件に合う予約可能な時間枠を検索"""
        logger.debug("=== find_available_slots デバッグ情報 ===")
        
        if duration_hours <= 0:
            raise StudioValidationError("利用時間は正の値である必要があります")
        
        result: List[StudioAvailability] = []
        min_duration_minutes = int(duration_hours * 60)
        
        for availability in self.availabilities:
            logger.debug(f"\n処理中のスタジオ: {availability.room_name}")
            start_minutes = self._start_minutes_map.get(availability.room_name, [0])
            allows_thirty_minute_slots = self._allows_thirty_minute_slots_map.get(
                availability.room_name, False
            )
            
            # 各開始時刻で利用可能な時間枠を収集
            all_valid_slots = set()
            for start_minute in start_minutes:
                valid_slots = self.filter_slots_in_range(
                    availability.time_slots,
                    desired_range,
                    min_duration_minutes,  # 常にユーザーが指定した予約時間を使用
                    start_minute
                )
                all_valid_slots.update(valid_slots)
                logger.debug(f"開始時刻 {start_minute}分の有効な時間枠: {len(valid_slots)}個")
            
            # 重複する時間枠をマージ
            merged_slots = self._merge_overlapping_slots(all_valid_slots)
            logger.debug(f"マージ後の時間枠: {len(merged_slots)}個")
            
            if merged_slots:
                result.append(StudioAvailability(
                    room_name=availability.room_name,
                    time_slots=merged_slots,
                    date=availability.date,
                    start_minutes=start_minutes,
                    allows_thirty_minute_slots=allows_thirty_minute_slots
                ))
        
        return result

    def _merge_overlapping_slots(self, slots: Set[StudioTimeSlot]) -> List[StudioTimeSlot]:
        """重複または連続する時間枠をマージ"""
        if not slots:
            return []
        
        # 時間枠をソート
        sorted_slots = sorted(slots, key=lambda x: (x.start_time, x.end_time))
        logger.debug("=== 時間枠マージ処理 ===")
        logger.debug(f"マージ前の時間枠: {[f'{s.start_time.strftime('%H:%M')}-{s.end_time.strftime('%H:%M')}' for s in sorted_slots]}")
        
        merged = []
        current = sorted_slots[0]
        
        for next_slot in sorted_slots[1:]:
            # 時間を分に変換して比較
            current_end = self._to_minutes(current.end_time, True)
            next_start = self._to_minutes(next_slot.start_time, False)
            next_end = self._to_minutes(next_slot.end_time, True)
            
            # 時間枠が重なるか連続している場合
            if next_start <= current_end:
                # 終了時刻を更新
                if next_end > current_end:
                    current = StudioTimeSlot(
                        start_time=current.start_time,
                        end_time=next_slot.end_time
                    )
            else:
                merged.append(current)
                current = next_slot
        
        merged.append(current)
        logger.debug(f"マージ後の時間枠: {[f'{s.start_time.strftime('%H:%M')}-{s.end_time.strftime('%H:%M')}' for s in merged]}")
        return merged
