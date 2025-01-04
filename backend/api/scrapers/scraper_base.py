# scraper_base.py
from typing import Protocol, List, Dict, Union
from datetime import date, time
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

    def to_dict(self) -> Dict[str, Union[str, List[Dict[str, str]]]]:
        """空き状況をJSON互換の辞書形式に変換"""
        return {
            "room_name": self.room_name,
            "date": self.date.isoformat(),
            "time_slots": [slot.to_dict() for slot in self.time_slots]
        }

class StudioScraperStrategy(Protocol):
    """スタジオスクレイパーのインターフェースを定義するプロトコル"""
    
    def establish_connection(self, shop_id: str) -> bool:
        """予約システムへの接続を確立する
        
        Args:
            shop_id: スタジオの店舗ID（必須）
            
        Returns:
            bool: 接続が成功したかどうか
            
        Raises:
            StudioConnectionError: 接続に失敗した場合
            StudioAuthenticationError: 認証に失敗した場合
        """
        ...

    def fetch_available_times(self, target_date: date) -> List[StudioAvailability]:
        """指定された日付の予約可能時間を取得する
        
        Args:
            target_date: 対象日付
            
        Returns:
            List[StudioAvailability]: 予約可能時間のリスト
            
        Raises:
            StudioScraperError: スクレイピングに失敗した場合
        """
        ...

    def to_json(self, availabilities: List[StudioAvailability], pretty: bool = True) -> str:
        """空き状況をJSON形式の文字列に変換する
        
        Args:
            availabilities: 空き状況のリスト
            pretty: 整形されたJSONを出力するかどうか
            
        Returns:
            str: JSON形式の文字列
            
        Raises:
            StudioParseError: JSON変換に失敗した場合
        """
        try:
            return json.dumps(
                [availability.to_dict() for availability in availabilities],
                ensure_ascii=False,
                indent=2 if pretty else None
            )
        except Exception as e:
            raise StudioParseError("JSONへの変換に失敗しました") from e