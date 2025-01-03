# scraper_base.py
from typing import Protocol, List, Dict, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import json
from pydantic import BaseModel, field_validator

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

class StudioTimeSlot(BaseModel):
    """スタジオの利用可能時間枠を表すモデル"""
    start_time: str  # HH:MM形式
    end_time: str    # HH:MM形式

    @field_validator('start_time', 'end_time')
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%H:%M")
            return v
        except ValueError:
            raise StudioValidationError(f"不正な時刻形式です: {v}. 期待される形式: HH:MM")

    @field_validator('end_time')
    @classmethod
    def validate_time_order(cls, v: str, info) -> str:
        if 'start_time' not in info.data:
            return v
            
        start = datetime.strptime(info.data['start_time'], "%H:%M")
        end = datetime.strptime(v, "%H:%M")
        
        start_minutes = start.hour * 60 + start.minute
        end_minutes = end.hour * 60 + end.minute
        
        if end_minutes == 0:
            end_minutes = 24 * 60
            
        if start_minutes >= end_minutes:
            raise StudioValidationError(
                f"開始時刻({info.data['start_time']})は終了時刻({v})より前である必要があります"
            )
        return v

    def to_dict(self) -> Dict[str, str]:
        return {
            "start": self.start_time,
            "end": self.end_time
        }

class StudioAvailability(BaseModel):
    """スタジオの空き状況を表すモデル"""
    room_name: str
    date: str  # YYYY-MM-DD形式
    time_slots: List[StudioTimeSlot]

    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise StudioValidationError(f"不正な日付形式です: {v}. 期待される形式: YYYY-MM-DD")

    def to_dict(self) -> Dict[str, Union[str, List[Dict[str, str]]]]:
        return {
            "room_name": self.room_name,
            "date": self.date,
            "time_slots": [slot.to_dict() for slot in self.time_slots]
        }

class StudioScraperStrategy(Protocol):
    """スタジオスクレイパーのインターフェースを定義するプロトコル"""
    
    def establish_connection(self, shop_id: Optional[str] = None) -> bool:
        """予約システムへの接続を確立する"""
        ...

    def fetch_available_times(self, date: str) -> List[StudioAvailability]:
        """指定された日付の予約可能時間を取得する"""
        ...

    def to_json(self, availabilities: List[StudioAvailability], pretty: bool = True) -> str:
        """空き状況をJSON形式の文字列に変換する"""
        try:
            return json.dumps(
                [availability.to_dict() for availability in availabilities],
                ensure_ascii=False,
                indent=2 if pretty else None
            )
        except Exception as e:
            raise StudioParseError("JSONへの変換に失敗しました", e)