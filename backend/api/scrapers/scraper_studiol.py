# scraper_studiol.py
import requests
import re
import json
from typing import List, Optional, Dict
from datetime import datetime, date, time, timedelta
import logging
from scraper_base import (
    StudioScraperStrategy,
    StudioScraperError,
    StudioTimeSlot,
    StudioAvailability
)
from scraper_registry import ScraperRegistry, ScraperMetadata

logger = logging.getLogger(__name__)

class StudioOLScraper(StudioScraperStrategy):
    """Studio-OLの予約システムに対応するスクレイパー実装"""
    
    BASE_URL = "https://studi-ol.com"
    TIME_SLOT_DURATION = 1800  # 30分（秒）
    
    def __init__(self):
        """初期化処理"""
        self.session: requests.Session = requests.Session()
        self._token: Optional[str] = None
        self.shop_id: Optional[str] = None
        self.room_name_map: Dict[str, str] = {}
    
    def establish_connection(self, shop_id: str) -> bool:
        """予約システムへの接続を確立し、トークンを取得する"""
        try:
            token = self._fetch_token(shop_id)
            self._set_connection_info(shop_id, token)
            logger.info(f"接続を確立しました: shop_id={shop_id}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"接続の確立に失敗: {str(e)}")
            raise StudioScraperError(f"接続の確立に失敗しました") from e

    def _fetch_token(self, shop_id: str) -> str:
        """ページからトークンとroom_name_mapを取得"""
        url = f"{self.BASE_URL}/shop/{shop_id}"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            if not response.text.strip():
                raise StudioScraperError("接続ページが空です")

            self._extract_room_info(response.text)
            token = self._extract_token(response.text)
            
            if not token:
                raise StudioScraperError("トークンの抽出に失敗しました")
                
            logger.debug(f"トークンを取得しました: {token[:10]}...")
            return token
            
        except requests.RequestException as e:
            raise StudioScraperError(f"トークンの取得に失敗しました") from e

    def _extract_room_info(self, html_content: str) -> None:
        """HTMLコンテンツから部屋情報を抽出"""
        room_pattern = r'resources:\s*\[(.*?)\]'
        room_match = re.search(room_pattern, html_content, re.DOTALL)
        if room_match:
            room_data = room_match.group(1)
            pairs = re.finditer(r'\{\s*id:\s*[\'"](\d+)[\'"]\s*,\s*title:\s*[\'"]([^\'"]+)[\'"]\s*\}', room_data)
            self.room_name_map = {pair.group(1): pair.group(2) for pair in pairs}
        
        if not self.room_name_map:
            logger.warning("部屋情報の抽出に失敗しました")

    def _extract_token(self, html_content: str) -> Optional[str]:
        """HTMLコンテンツからトークンを抽出"""
        match = re.search(r'name="_token" value="([^"]+)"', html_content)
        return match.group(1) if match else None

    def _set_connection_info(self, shop_id: str, token: str) -> None:
        """接続情報を設定"""
        self._token = token
        self.shop_id = shop_id
        logger.debug(f"接続情報を設定: shop_id={shop_id}")

    def fetch_available_times(self, target_date: date) -> List[StudioAvailability]:
        """指定された日付の予約可能時間を取得"""
        if not self._token or not self.shop_id:
            raise StudioScraperError("先にestablish_connectionを呼び出してください")
        
        logger.info(f"予約可能時間の取得を開始: date={target_date}")
        schedule_data = self._fetch_raw_schedule_data(target_date)
        return self._parse_schedule_data(schedule_data, target_date)

    def _fetch_raw_schedule_data(self, target_date: date) -> List[dict]:
        """APIから生のスケジュールデータを取得"""
        url = f"{self.BASE_URL}/get_schedule_shop"
        headers, data = self._prepare_schedule_request(target_date)
        
        try:
            response = self._make_schedule_request(url, headers, data)
            return self._parse_response(response)
        except requests.RequestException as e:
            raise StudioScraperError("スケジュールデータの取得に失敗しました") from e
        except json.JSONDecodeError as e:
            raise StudioScraperError("スケジュールデータのパースに失敗しました") from e

    def _prepare_schedule_request(self, target_date: date) -> tuple[dict, dict]:
        """スケジュールリクエストのヘッダーとデータを準備"""
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        }
        
        assert self._token is not None  # 型チェックのため
        assert self.shop_id is not None  # 型チェックのため
        
        date_str = target_date.isoformat()
        data = {
            "_token": self._token,
            "shop_id": self.shop_id,
            "start": f"{date_str} 00:00:00",
            "end": f"{date_str} 23:30:00"
        }
        
        logger.debug(f"リクエストデータを準備: date={date_str}")
        return headers, data

    def _make_schedule_request(self, url: str, headers: dict, data: dict) -> requests.Response:
        """スケジュールデータのリクエストを実行"""
        response = self.session.post(url, headers=headers, data=data)
        response.raise_for_status()
        return response

    def _parse_response(self, response: requests.Response) -> List[dict]:
        """レスポンスをパースしてJSONデータを取得"""
        if not response.text.strip():
            raise StudioScraperError("スケジュールデータが空です")
        
        return response.json()

    def _parse_schedule_data(
        self,
        schedule_data: List[dict],
        target_date: date
    ) -> List[StudioAvailability]:
        """スケジュールデータをパースして利用可能時間を抽出"""
        studio_time_slots = self._group_time_slots_by_studio(schedule_data)
        logger.debug(f"スタジオ数: {len(studio_time_slots)}")
        return self._create_studio_availabilities(studio_time_slots, target_date)

    def _group_time_slots_by_studio(
        self,
        schedule_data: List[dict]
    ) -> Dict[str, List[datetime]]:
        """スタジオごとに時間枠をグループ化"""
        studio_time_slots: Dict[str, List[datetime]] = {}
        
        for entry in schedule_data:
            room_id = str(entry['roomId'])
            room_name = self.room_name_map.get(room_id, f"Room {room_id}")
            start_dt = datetime.fromisoformat(entry['start'])
            
            if room_name not in studio_time_slots:
                studio_time_slots[room_name] = []
            
            studio_time_slots[room_name].append(start_dt)
        
        return studio_time_slots

    def _create_studio_availabilities(
        self,
        studio_time_slots: Dict[str, List[datetime]],
        target_date: date
    ) -> List[StudioAvailability]:
        """スタジオごとの利用可能時間を作成"""
        studio_availabilities = []
        
        for studio_name, time_slots in studio_time_slots.items():
            merged_slots = self._merge_consecutive_slots(sorted(time_slots))
            studio_availabilities.append(
                StudioAvailability(
                    room_name=studio_name,
                    time_slots=merged_slots,
                    date=target_date
                )
            )
            logger.debug(f"スタジオ {studio_name} の利用可能枠: {len(merged_slots)}個")
        
        return studio_availabilities

    def _merge_consecutive_slots(self, time_slots: List[datetime]) -> List[StudioTimeSlot]:
        """連続した時間枠をマージ"""
        merged_slots = []
        if not time_slots:
            return merged_slots
            
        slot_start = time_slots[0]
        prev_time = slot_start
        
        for curr_time in time_slots[1:]:
            if (curr_time - prev_time).total_seconds() > self.TIME_SLOT_DURATION:
                merged_slots.append(self._create_time_slot(slot_start, prev_time))
                slot_start = curr_time
            prev_time = curr_time
        
        merged_slots.append(self._create_time_slot(slot_start, prev_time))
        return merged_slots

    def _create_time_slot(self, start: datetime, end: datetime) -> StudioTimeSlot:
        """時間枠オブジェクトを作成"""
        start_time = time(hour=start.hour, minute=start.minute)
        end_time = (end + timedelta(minutes=30)).time()
        
        return StudioTimeSlot(
            start_time=start_time,
            end_time=end_time
        )

def register(registry: ScraperRegistry) -> None:
    """Studio-OLスクレイパーの登録"""
    registry.register_strategy(
        'studio_ol',
        StudioOLScraper,
        ScraperMetadata(
            description="Studio-OL予約システム用スクレイパー",
            version="1.0.0",
            requires_auth=False,
            base_url="https://studi-ol.com"
        )
    )