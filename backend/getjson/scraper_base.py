from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional, Union
import json

@dataclass
class StudioTimeSlot:
    """スタジオの予約可能な時間枠を表すデータクラス"""
    start_time: str  # HH:MM形式
    end_time: str    # HH:MM形式

    def __post_init__(self):
        """時刻形式の検証を行う"""
        self._validate_time_format(self.start_time)
        self._validate_time_format(self.end_time)
        self._validate_time_order()
        
    @staticmethod
    def _validate_time_format(time_str: str) -> None:
        """時刻形式が正しいかを検証"""
        try:
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            raise ValueError(f"Invalid time format: {time_str}. Expected format: HH:MM")

    def _validate_time_order(self) -> None:
        """開始時刻が終了時刻より前かを検証（24時間表記対応）"""
        start = datetime.strptime(self.start_time, "%H:%M")
        end = datetime.strptime(self.end_time, "%H:%M")
        
        # 時刻を分単位に変換
        start_minutes = start.hour * 60 + start.minute
        end_minutes = end.hour * 60 + end.minute
        
        # 終了時刻が00:00の場合は24:00（1440分）として扱う
        if end_minutes == 0:
            end_minutes = 24 * 60
            
        if start_minutes >= end_minutes:
            raise ValueError(
                f"Start time ({self.start_time}) must be earlier than end time ({self.end_time})"
            )

    def to_dict(self) -> Dict[str, str]:
        """辞書形式に変換"""
        return {
            "start": self.start_time,
            "end": self.end_time
        }

@dataclass
class StudioAvailability:
    """スタジオの空き状況を表すデータクラス"""
    room_name: str
    time_slots: List[StudioTimeSlot]
    date: str  # YYYY-MM-DD形式

    def __post_init__(self):
        """日付形式の検証を行う"""
        self._validate_date_format(self.date)
        self._validate_time_slots()

    @staticmethod
    def _validate_date_format(date_str: str) -> None:
        """日付形式が正しいかを検証"""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Expected format: YYYY-MM-DD")

    def _validate_time_slots(self) -> None:
        """時間枠が空でないことを検証"""
        if not isinstance(self.time_slots, list):
            raise ValueError("time_slots must be a list")
        
        if not all(isinstance(slot, StudioTimeSlot) for slot in self.time_slots):
            raise ValueError("all elements in time_slots must be StudioTimeSlot instances")

    def to_dict(self) -> Dict[str, Union[str, List[Dict[str, str]]]]:
        """辞書形式に変換"""
        return {
            "room_name": self.room_name,
            "date": self.date,
            "time_slots": [slot.to_dict() for slot in self.time_slots]
        }

class StudioScraperError(Exception):
    """スタジオスクレイパーの基本例外クラス"""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error

    def __str__(self) -> str:
        if self.original_error:
            return f"{super().__str__()} (Original error: {str(self.original_error)})"
        return super().__str__()

class StudioScraperBase(ABC):
    """スタジオ予約システムスクレイパーの抽象基底クラス"""
    
    @abstractmethod
    def establish_connection(self, shop_id: Optional[str] = None) -> bool:
        """
        予約システムへの接続を確立し、セッションを初期化する
        
        Args:
            shop_id: チェーン店舗の場合の店舗ID。単独店舗の場合はNone
        
        Returns:
            bool: 接続確立成功時True
            
        Raises:
            StudioScraperError: 接続処理でエラーが発生した場合
        """
        pass

    @abstractmethod
    def fetch_available_times(self, date: str) -> List[StudioAvailability]:
        """
        指定された日付の予約可能時間を取得
        
        Args:
            date: YYYY-MM-DD形式の日付
            
        Returns:
            List[StudioAvailability]: 予約可能時間のリスト
            
        Raises:
            StudioScraperError: スクレイピング処理でエラーが発生した場合
        """
        pass

    def validate_date(self, date: str) -> None:
        """日付形式の検証を行う共通メソッド"""
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise StudioScraperError(f"Invalid date format: {date}. Expected format: YYYY-MM-DD")

    def validate_time_format(self, time: str) -> None:
        """時刻形式の検証を行う共通メソッド"""
        try:
            datetime.strptime(time, "%H:%M")
        except ValueError:
            raise StudioScraperError(f"Invalid time format: {time}. Expected format: HH:MM")

    def to_json(self, availabilities: List[StudioAvailability], pretty: bool = True) -> str:
        """空き状況をJSON形式の文字列に変換"""
        try:
            return json.dumps(
                [availability.to_dict() for availability in availabilities],
                ensure_ascii=False,
                indent=2 if pretty else None
            )
        except Exception as e:
            raise StudioScraperError("Failed to convert to JSON", e)