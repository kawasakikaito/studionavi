from typing import List, Optional, Dict, Set, Any, Union, Protocol
from datetime import date, time, datetime, timedelta
import requests
import re
import json
import logging
from pathlib import Path
from bs4 import BeautifulSoup
from pydantic import BaseModel, field_validator
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryError
)
from functools import wraps
from dataclasses import dataclass
from enum import Enum, auto
import functools
from importlib.util import spec_from_file_location, module_from_spec
import sys
import glob
import os

logger = logging.getLogger(__name__)

# Base exceptions
class StudioScraperError(Exception):
    """スクレイパーの基本例外クラス"""
    pass

class StudioConnectionError(StudioScraperError):
    """接続失敗時に発生する例外"""
    pass

class StudioAuthenticationError(StudioScraperError):
    """認証失敗時に発生する例外"""
    pass

class StudioParseError(StudioScraperError):
    """データ解析失敗時に発生する例外"""
    pass

class StudioValidationError(StudioScraperError):
    """バリデーション失敗時に発生する例外"""
    pass

# Base models
class StudioTimeSlot(BaseModel):
    """スタジオの利用可能時間枠を表すモデル"""
    start_time: time
    end_time: time
    
    class Config:
        frozen = True  # イミュータブルにする
        
    @field_validator('end_time')
    @classmethod
    def validate_time_order(cls, end: time, info) -> time:
        if 'start_time' not in info.data:
            return end
            
        start = info.data['start_time']
        start_minutes = start.hour * 60 + start.minute
        end_minutes = end.hour * 60 + end.minute
        
        # 終了時刻が深夜0時以降の場合（例：00:30）は24時間を加算
        if end_minutes < start_minutes:
            end_minutes += 24 * 60
            
        if start_minutes >= end_minutes:
            raise StudioValidationError(
                f"開始時刻({start.strftime('%H:%M')})は"
                f"終了時刻({end.strftime('%H:%M')})より前である必要があります"
            )
        return end

    def _to_minutes(self) -> tuple[int, int]:
        """開始時刻と終了時刻を分単位に変換"""
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        
        # 終了時刻が深夜0時以降の場合は24時間を加算
        if end_minutes < start_minutes:
            end_minutes += 24 * 60
            
        return start_minutes, end_minutes
    
    def get_duration_minutes(self) -> int:
        """時間枠の長さを分単位で取得"""
        start_minutes, end_minutes = self._to_minutes()
        return end_minutes - start_minutes

    def overlaps_with(self, other: 'StudioTimeSlot') -> bool:
        """別の時間枠と重複するかどうかを確認"""
        self_start, self_end = self._to_minutes()
        other_start, other_end = other._to_minutes()
        return max(self_start, other_start) < min(self_end, other_end)

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
        valid_minutes = {0, 30}
        invalid_minutes = set(v) - valid_minutes
        if invalid_minutes:
            raise StudioValidationError(
                f"無効な開始時刻（分）が含まれています: {invalid_minutes}\n"
                "開始時刻（分）は0または30である必要があります"
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

class StudioScraperStrategy(Protocol):
    """スタジオスクレイパーの基底クラス"""
    
    BASE_URL: str
    MAX_RETRIES = 3
    MIN_WAIT = 4
    MAX_WAIT = 10
    
    def __init__(self):
        self.session: requests.Session = requests.Session()
        self._configure_retry_policy()
    
    def _configure_retry_policy(self):
        """リトライポリシーの設定"""
        self._retry_decorator = retry(
            stop=stop_after_attempt(self.MAX_RETRIES),
            wait=wait_exponential(multiplier=1, min=self.MIN_WAIT, max=self.MAX_WAIT),
            retry=retry_if_exception_type((
                requests.ConnectionError,
                requests.Timeout,
                requests.HTTPError
            )),
            before_sleep=before_sleep_log(logger, logging.INFO)
        )
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """共通のリクエストメソッド"""
        @wraps(self._make_request)
        @self._retry_decorator
        def _wrapped_request():
            try:
                response = self.session.request(
                    method, 
                    url, 
                    timeout=(10, 30),  # 接続タイムアウト, 読み取りタイムアウト
                    **kwargs
                )
                response.raise_for_status()
                return response
                
            except requests.Timeout as e:
                logger.error(f"リクエストがタイムアウト: {str(e)}")
                raise StudioScraperError("リクエストがタイムアウトしました") from e
                
            except requests.HTTPError as e:
                status_code = e.response.status_code if e.response else "不明"
                logger.error(f"HTTPエラー({status_code}): {str(e)}")
                raise StudioScraperError(f"HTTPエラー({status_code})が発生しました") from e
                
            except requests.ConnectionError as e:
                logger.error(f"接続エラー: {str(e)}")
                raise StudioScraperError("接続エラーが発生しました") from e
                
            except requests.RequestException as e:
                logger.error(f"リクエストエラー: {str(e)}")
                raise StudioScraperError("リクエストに失敗しました") from e
        
        try:
            return _wrapped_request()
        except RetryError as e:
            logger.error(f"リトライ上限に到達: {str(e)}")
            raise StudioScraperError("リトライ後も要求が失敗しました") from e

    def establish_connection(self, shop_id: str) -> bool:
        """予約システムへの接続を確立する（各スクレイパーで実装）"""
        raise NotImplementedError

    def fetch_available_times(self, target_date: date) -> List[StudioAvailability]:
        """指定された日付の予約可能時間を取得する（各スクレイパーで実装）"""
        raise NotImplementedError

    def _merge_consecutive_slots(self, time_slots: List[datetime]) -> List[StudioTimeSlot]:
        """連続または重複する時間枠をマージ"""
        merged_slots = []
        if not time_slots:
            return merged_slots
            
        # 時間枠をソート
        sorted_slots = sorted(time_slots)
        
        # マージ処理の初期化
        slot_start = sorted_slots[0]
        current_end = slot_start + timedelta(minutes=30)
        
        for current_time in sorted_slots[1:]:
            # 現在の終了時刻と次のスロットの開始時刻を比較
            next_slot_end = current_time + timedelta(minutes=30)
            
            # 時間を分単位に変換して比較
            current_end_minutes = (current_end.hour * 60 + current_end.minute) % (24 * 60)
            current_time_minutes = (current_time.hour * 60 + current_time.minute) % (24 * 60)
            
            # 深夜0時をまたぐ場合の調整
            if current_time_minutes < current_end_minutes:
                current_time_minutes += 24 * 60
                
            if current_time_minutes <= current_end_minutes:
                # 重複または連続している場合は終了時刻を更新
                current_end = max(current_end, next_slot_end)
            else:
                # 重複も連続もしていない場合は新しいスロットを作成
                merged_slots.append(self._create_time_slot(slot_start, current_end))
                slot_start = current_time
                current_end = next_slot_end
        
        # 最後の時間枠を追加
        merged_slots.append(self._create_time_slot(slot_start, current_end))
        
        return merged_slots

    def _create_time_slot(self, start: datetime, end: datetime) -> StudioTimeSlot:
        """時間枠オブジェクトを作成"""
        start_time = time(hour=start.hour, minute=start.minute)
        end_time = time(hour=end.hour % 24, minute=end.minute)  # 24時以降の処理を修正
        
        return StudioTimeSlot(
            start_time=start_time,
            end_time=end_time
        )

    def to_json(self, availabilities: List[StudioAvailability], pretty: bool = True) -> str:
        """空き状況をJSON形式の文字列に変換"""
        try:
            return json.dumps(
                [availability.to_dict() for availability in availabilities],
                ensure_ascii=False,
                indent=2 if pretty else None
            )
        except Exception as e:
            raise StudioParseError("JSONへの変換に失敗しました") from e

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
        
        # 終了時刻が深夜0時以降の場合は24時間を加算
        if end_minutes < start_minutes:
            end_minutes += 24 * 60
            
        if start_minutes >= end_minutes:
            raise StudioValidationError(
                f"開始時刻({start.strftime('%H:%M')})は"
                f"終了時刻({end.strftime('%H:%M')})より前である必要があります"
            )

class AvailabilityChecker:
    """予約可能時間をチェックするクラス"""

    def __init__(self, availabilities: List[StudioAvailability]):
        self.availabilities = availabilities
        self._start_minutes_map: Dict[str, List[int]] = {}
        self._allows_thirty_minute_slots_map: Dict[str, bool] = {}
        
        for availability in availabilities:
            self._start_minutes_map[availability.room_name] = availability.start_minutes
            self._allows_thirty_minute_slots_map[availability.room_name] = availability.allows_thirty_minute_slots

    def _combine_date_time(self, d: date, t: time) -> datetime:
        """日付と時刻を組み合わせてdatetimeオブジェクトを作成"""
        return datetime.combine(d, t)

    def _to_minutes(self, t: time, is_end_time: bool = False) -> int:
        """時刻を分単位に変換"""
        minutes = t.hour * 60 + t.minute
        if minutes == 0 and is_end_time:
            return 24 * 60
        return minutes

    def find_available_slots(
        self,
        desired_range: TimeRange,
        duration_hours: float
    ) -> List[StudioAvailability]:
        """指定された条件に合う予約可能な時間枠を検索"""
        if duration_hours <= 0:
            raise StudioValidationError("利用時間は正の値である必要があります")
        
        result: List[StudioAvailability] = []
        min_duration_minutes = int(duration_hours * 60)
        
        for availability in self.availabilities:
            start_minutes = self._start_minutes_map.get(availability.room_name, [0])
            allows_thirty_minute_slots = self._allows_thirty_minute_slots_map.get(
                availability.room_name, False
            )
            
            filtered_slots = []
            for slot in availability.time_slots:
                slot_duration = (
                    self._to_minutes(slot.end_time, True) -
                    self._to_minutes(slot.start_time, False)
                )
                
                valid_for_any_start = False
                for start_minute in start_minutes:
                    adjusted_duration = slot_duration
                    if start_minute > 0:
                        adjusted_duration -= start_minute
                    
                    if allows_thirty_minute_slots:
                        if adjusted_duration >= 30:
                            valid_for_any_start = True
                            break
                    else:
                        if adjusted_duration >= min_duration_minutes:
                            valid_for_any_start = True
                            break
                
                if valid_for_any_start:
                    filtered_slots.append(slot)
            
            if filtered_slots:
                valid_slots = self._filter_slots_in_range(
                    filtered_slots,
                    desired_range,
                    30 if allows_thirty_minute_slots else min_duration_minutes
                )
                
                if valid_slots:
                    result.append(StudioAvailability(
                        room_name=availability.room_name,
                        time_slots=valid_slots,
                        date=availability.date,
                        start_minutes=start_minutes,
                        allows_thirty_minute_slots=allows_thirty_minute_slots
                    ))
        
        return result

    def _filter_slots_in_range(
        self,
        slots: List[StudioTimeSlot],
        desired_range: TimeRange,
        min_duration_minutes: int
    ) -> List[StudioTimeSlot]:
        """指定された時間範囲内の時間枠をフィルタリング"""
        filtered = []
        range_start = self._to_minutes(desired_range.start, False)
        range_end = self._to_minutes(desired_range.end, True)
        
        for slot in slots:
            slot_start = self._to_minutes(slot.start_time, False)
            slot_end = self._to_minutes(slot.end_time, True)
            
            if slot_start < range_end and slot_end > range_start:
                new_start_minutes = max(slot_start, range_start)
                new_end_minutes = min(slot_end, range_end)
                
                if new_end_minutes - new_start_minutes >= min_duration_minutes:
                    # minutes を time オブジェクトに変換
                    new_start = time(
                        (new_start_minutes % 1440) // 60,
                        new_start_minutes % 60
                    )
                    
                    if new_end_minutes == 24 * 60:
                        new_end = time(0, 0)
                    else:
                        new_end = time(
                            (new_end_minutes % 1440) // 60,
                            new_end_minutes % 60
                        )
                    
                    filtered.append(StudioTimeSlot(
                        start_time=new_start,
                        end_time=new_end
                    ))
        
        return filtered