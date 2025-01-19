from typing import Protocol, List, Dict, Optional, Union
from datetime import date, time, datetime, timedelta
from pydantic import BaseModel, field_validator
import json
import logging
import requests
from functools import wraps
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryError
)

logger = logging.getLogger(__name__)

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
    start_minute: int = 0

    @field_validator('start_minute')
    @classmethod
    def validate_start_minute(cls, v: int) -> int:
        if v >= 60 or v < 0:
            raise StudioValidationError("開始時刻（分）は0以上60未満である必要があります")
        return v

    def to_dict(self) -> Dict[str, Union[str, List[Dict[str, str]], int]]:
        return {
            "room_name": self.room_name,
            "date": self.date.isoformat(),
            "time_slots": [slot.to_dict() for slot in self.time_slots],
            "start_minute": self.start_minute
        }

class StudioScraperStrategy(Protocol):
    """スタジオスクレイパーの基底クラス"""
    
    # デフォルトの設定
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
            before_sleep=before_sleep_log(logger, logging.INFO),
            after=self._log_retry_stats
        )
    
    def _log_retry_stats(self, retry_state):
        """リトライの統計情報をログに記録"""
        if retry_state.attempt_number > 1:
            logger.info(
                f"リトライ試行 {retry_state.attempt_number}/{self.MAX_RETRIES} "
                f"経過時間: {retry_state.seconds_since_start:.1f}秒"
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
