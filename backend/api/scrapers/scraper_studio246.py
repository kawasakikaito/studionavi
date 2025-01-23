from typing import List, Optional, Dict, Tuple
import requests
import re
import json
from datetime import datetime, date, time, timedelta
import logging
from bs4 import BeautifulSoup
from pathlib import Path
from api.scrapers.scraper_base import (
    StudioScraperStrategy,
    StudioScraperError,
    StudioTimeSlot,
    StudioAvailability,
    StudioValidationError
)
from api.scrapers.scraper_registry import ScraperRegistry, ScraperMetadata
from config.logging_config import setup_logger
from pydantic import field_validator

logger = setup_logger(__name__)

class Studio246ConnectionManager:
    """Studio246の接続管理クラス"""
    
    BASE_URL = "https://www.studio246.net/reserve/"
    AJAX_URL = "https://www.studio246.net/reserve/ajax/ajax_timeline_contents.php"
    
    def __init__(self):
        self._token: Optional[str] = None
        self.shop_id: Optional[str] = None
        
    def establish_connection(self, shop_id: str) -> bool:
        """接続を確立し、トークンを取得"""
        try:
            self._token = self._fetch_token(shop_id)
            self.shop_id = shop_id
            return True
        except Exception as e:
            raise StudioScraperError(f"接続の確立に失敗: {str(e)}") from e
            
    def _fetch_token(self, shop_id: str) -> str:
        """PHPSESSIDトークンを取得"""
        url = f"{self.BASE_URL}?si={shop_id}"
        response = requests.get(url)
        response.raise_for_status()
        
        # CookieからPHPSESSIDを取得
        phpsessid = response.cookies.get('PHPSESSID')
        if not phpsessid:
            raise StudioScraperError("セッションIDの取得に失敗")
            
        return phpsessid
        
    def get_request_headers(self) -> Dict[str, str]:
        """リクエストヘッダーを取得"""
        return {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Cookie': f'PHPSESSID={self._token}'
        }

class Studio246Scraper(StudioScraperStrategy):
    """Studio246の予約システムに対応するスクレイパー実装"""
    
    MAX_RETRIES = 5
    MIN_WAIT = 3
    MAX_WAIT = 15
    TIME_SLOT_DURATION = 1800  # 30分（秒）
    
    def __init__(self):
        """初期化処理"""
        super().__init__()
        self.connection = Studio246ConnectionManager()
        self.room_name_map: Dict[str, str] = {}
        self.start_minutes_map: Dict[str, List[int]] = {}
        self.thirty_minute_slots_map: Dict[str, bool] = {}

    def establish_connection(self, shop_id: str) -> bool:
        """予約システムへの接続を確立"""
        return self.connection.establish_connection(shop_id)

    def fetch_available_times(self, target_date: date) -> List[StudioAvailability]:
        """指定された日付の予約可能時間を取得"""
        schedule_data = self._fetch_schedule_data(target_date)
        time_slots = self._parse_schedule_data(schedule_data, target_date)
        return self._create_availabilities(time_slots, target_date)
        
    def _fetch_schedule_data(self, target_date: date) -> List[dict]:
        """スケジュールデータを取得"""
        headers = self.connection.get_request_headers()
        data = {
            'si': self.connection.shop_id,
            'date': target_date.strftime('%Y-%m-%d')
        }
        
        response = requests.post(
            self.connection.AJAX_URL,
            headers=headers,
            data=data
        )
        response.raise_for_status()
        
        return self._parse_schedule_html(response.text, target_date)

    def _parse_schedule_html(self, html_content: str, target_date: date) -> List[dict]:
        """HTMLからスケジュールデータを抽出"""
        soup = BeautifulSoup(html_content, 'html.parser')
        timeline_blocks = soup.find_all('div', class_='timeline_block')
        
        for block in timeline_blocks:
            block_date_str = block.get('data-date')
            if block_date_str and datetime.strptime(block_date_str, '%Y-%m-%d').date() == target_date:
                return self._extract_available_slots(block)
                
        return []

    def _extract_available_slots(self, timeline_block: BeautifulSoup) -> List[dict]:
        """利用可能な時間枠を抽出"""
        slots = []
        
        for cell in timeline_block.find_all('td'):
            if self._is_available_cell(cell):
                time_str = cell.get('data-time')
                if time_str:
                    slots.append({
                        'studio_id': '1',
                        'start_time': time_str,
                        'is_available': True
                    })
                    
        return slots

    def _is_available_cell(self, cell) -> bool:
        """セルが予約可能か判定"""
        cell_classes = cell.get('class', [])
        cell_state = cell.get('state')
        
        return (
            'time_cell' in cell_classes and
            'bg_black' not in cell_classes and
            cell_state == 'posi'
        )

    def _parse_time_slot(self, time_str: str, target_date: date) -> datetime:
        """時刻文字列をdatetimeに変換"""
        hour = int(time_str.split(':')[0])
        minute = int(time_str.split(':')[1])
        
        # 24:00以降の時間は次の日の予約として扱う
        slot_date = target_date
        if hour >= 24:
            hour -= 24
            slot_date += timedelta(days=1)
            
        return datetime.combine(
            slot_date,
            time(hour, minute)
        )

    def _prepare_schedule_request(self, target_date: date) -> tuple:
        """スケジュールリクエストのヘッダーとデータを準備"""
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Cookie': f'PHPSESSID={self._token}'
        }
        
        data = {
            'si': self.shop_id,
            'date': target_date.strftime('%Y-%m-%d')
        }
        
        return headers, data

    def _parse_schedule_data(self, schedule_data: List[dict], target_date: date) -> Dict[str, List[datetime]]:
        """
        スケジュールデータを解析し、時間枠を整理
        
        Args:
            schedule_data: スケジュールデータのリスト
            target_date: 対象日付
            
        Returns:
            スタジオIDをキー、時間枠リストを値とする辞書
            
        Raises:
            StudioScraperError: データ解析に失敗した場合
        """
        time_slots: Dict[str, List[datetime]] = {}
        
        if not schedule_data:
            logger.debug("スケジュールデータが空です")
            return time_slots
            
        logger.info(f"スケジュールデータの解析を開始: 件数={len(schedule_data)}")
        
        for idx, item in enumerate(schedule_data):
            try:
                # 時間枠データを解析
                start_time = self._parse_time_slot(item['start_time'], target_date)
                minute = start_time.minute
                
                # 開始時刻（分）に基づいてスタジオIDを設定
                studio_id = str(minute)  # 0, 15, 30, 45分の部屋に対応
                
                if studio_id not in time_slots:
                    time_slots[studio_id] = []
                time_slots[studio_id].append(start_time)
                
                logger.debug(f"時間枠を追加: index={idx}, studio_id={studio_id}, start_time={start_time}")
                
            except (KeyError, ValueError) as e:
                logger.warning(f"無効な時間枠データをスキップ: index={idx}, item={item}, エラー: {str(e)}")
                continue
                
        logger.info(f"スケジュールデータの解析が完了: 有効な時間枠数={sum(len(v) for v in time_slots.values())}")
        return time_slots

    def _create_availabilities(self, time_slots: Dict[str, List[datetime]], target_date: date) -> List[StudioAvailability]:
        """
        利用可能時間リストを作成
        
        Args:
            time_slots: スタジオIDをキー、時間枠リストを値とする辞書
            target_date: 対象日付
            
        Returns:
            利用可能時間のリスト
            
        Raises:
            StudioScraperError: 利用可能時間の作成に失敗した場合
        """
        availabilities: List[StudioAvailability] = []
        
        if not time_slots:
            logger.warning("利用可能な時間枠がありません")
            return availabilities
            
        logger.info(f"利用可能時間の作成を開始: スタジオ数={len(time_slots)}")
        
        for studio_id, slots in time_slots.items():
            if not slots:
                logger.debug(f"空の時間枠をスキップ: studio_id={studio_id}")
                continue
                
            try:
                # 時間枠オブジェクトを作成
                time_slot_objects = [
                    StudioTimeSlot(
                        start_time=time(slot.hour, slot.minute),
                        end_time=time((slot.hour + 1) % 24, slot.minute)
                    )
                    for slot in sorted(set(slots))  # 重複排除とソート
                ]
                
                # 利用可能時間を作成
                minute = int(studio_id)
                availability = StudioAvailability(
                    room_name=f"Room {minute}",
                    date=target_date,
                    time_slots=time_slot_objects,
                    start_minutes=[minute],
                    allows_thirty_minute_slots=False,
                    valid_start_minutes={0, 15, 30, 45}
                )
                availabilities.append(availability)
                
                logger.debug(f"利用可能時間を作成: studio_id={studio_id}, 時間枠数={len(time_slot_objects)}")
                
            except Exception as e:
                error_msg = f"利用可能時間の作成に失敗: studio_id={studio_id}, エラー: {str(e)}"
                logger.error(error_msg)
                raise StudioScraperError(error_msg) from e
                
        logger.info(f"利用可能時間の作成が完了: 件数={len(availabilities)}")
        return availabilities

    def _parse_time_slot(self, time_str: str, target_date: date) -> datetime:
        """
        時刻文字列をdatetimeに変換
        
        Args:
            time_str: 時刻文字列 (HH:MM形式)
            target_date: 対象日付
            
        Returns:
            変換されたdatetimeオブジェクト
            
        Raises:
            ValueError: 時刻文字列の形式が不正な場合
            StudioScraperError: 時刻の変換に失敗した場合
        """
        try:
            hour, minute = map(int, time_str.split(':'))
            
            # 24:00以降の時間は次の日の予約として扱う
            slot_date = target_date
            if hour >= 24:
                hour -= 24
                slot_date += timedelta(days=1)
                
            result = datetime.combine(slot_date, time(hour, minute))
            logger.debug(f"時刻を変換: time_str={time_str} -> datetime={result}")
            return result
            
        except (ValueError, IndexError) as e:
            error_msg = f"時刻のパースに失敗: time_str={time_str}, エラー: {str(e)}"
            logger.error(error_msg)
            raise StudioScraperError(error_msg) from e

def register(registry: ScraperRegistry) -> None:
    """Studio246スクレイパーの登録"""
    registry.register_strategy(
        'studio246',  # スクレイパーの識別子
        Studio246Scraper,
        ScraperMetadata(
            description="Studio246の予約システム",
            version="1.0.0",
            requires_auth=False,
            base_url="https://www.studio246.net/reserve/"
        )
    )
