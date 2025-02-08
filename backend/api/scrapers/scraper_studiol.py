from typing import List, Optional, Dict, Set
import requests
import re
import json
from datetime import datetime, date, time, timedelta
import logging
from pathlib import Path
from api.scrapers.scraper_base import (
    StudioScraperStrategy,
    StudioScraperError,
    StudioTimeSlot,
    StudioAvailability
)
from api.scrapers.scraper_registry import ScraperRegistry, ScraperMetadata
from config.logging_config import setup_logger

logger = setup_logger(__name__)

class StudiolScraper(StudioScraperStrategy):
    """Studiolの予約システムに対応するスクレイパー実装"""
    
    BASE_URL = "https://studi-ol.com"
    MAX_RETRIES = 5
    MIN_WAIT = 3
    MAX_WAIT = 15
    TIME_SLOT_DURATION = 1800  # 30分（秒）
    
    def __init__(self):
        """初期化処理"""
        super().__init__()
        self._token: Optional[str] = None
        self.shop_id: Optional[str] = None
        self.room_name_map: Dict[str, str] = {}
        self.start_minutes_map: Dict[str, List[int]] = {}  # 複数の開始時刻を管理
        self.thirty_minute_slots_map: Dict[str, bool] = {}
        
        logger.debug(f"初期化パラメータ: base_url={self.BASE_URL}")
        logger.info("StudiolScraperの初期化が完了")

    def establish_connection(self, shop_id: str) -> bool:
        """予約システムへの接続を確立し、トークンを取得する"""
        try:
            token = self._fetch_token(shop_id)
            self._set_connection_info(shop_id, token)
            logger.info(f"接続確立を開始: shop_id={shop_id}")
            logger.info(f"接続確立が完了: shop_id={shop_id}")
            return True
        except StudioScraperError:
            logger.error(f"接続確立に失敗: shop_id={shop_id}")
            raise
        except Exception as e:
            logger.error(f"接続確立で予期せぬエラーが発生: shop_id={shop_id}, エラー: {str(e)}")
            raise StudioScraperError("接続の確立に失敗しました") from e

    def _fetch_token(self, shop_id: str) -> str:
        """ページからトークンを取得"""
        url = f"{self.BASE_URL}/shop/{shop_id}"
        try:
            response = self._make_request("GET", url)
            
            if not response.text.strip():
                raise StudioScraperError("接続ページが空です")
                
            self._extract_room_info(response.text)
            token = self._extract_token(response.text)
            
            if not token:
                raise StudioScraperError("トークンの抽出に失敗しました")
                
            logger.debug(f"トークンを取得しました: {token[:10]}...")
            return token
            
        except StudioScraperError:
            raise
        except Exception as e:
            logger.error(f"予期せぬエラー: {str(e)}")
            raise StudioScraperError("トークンの取得に失敗しました") from e

    def _extract_room_info(self, html_content: str) -> None:
        """HTMLコンテンツから部屋情報を抽出"""
        room_pattern = r'resources:\s*\[(.*?)\]'
        room_match = re.search(room_pattern, html_content, re.DOTALL)
        
        # 部屋名と部屋IDのマッピング
        self.room_name_map = {}
        # 開始時刻（分）マップ（複数の値を保持）
        self.start_minutes_map = {}
        # 30分単位予約フラグマップ
        self.thirty_minute_slots_map = {}
        
        if room_match:
            room_data = room_match.group(1)
            # 部屋名とIDのマッピングを抽出
            pairs = re.finditer(r'\{\s*id:\s*[\'"](\d+)[\'"]\s*,\s*title:\s*[\'"]([^\'"]+)[\'"]\s*\}', room_data)
            self.room_name_map = {pair.group(1): pair.group(2) for pair in pairs}
            
            # room-tabからstartTime属性を含む部屋情報を抽出
            room_tabs = re.finditer(r'<li[^>]*?room-id="(\d+)"[^>]*?startTime="(\d+)"[^>]*?>', html_content)
            
            for tab in room_tabs:
                room_id = tab.group(1)
                try:
                    start_time = int(tab.group(2))
                    # startTime=60の場合は[0, 30]として保持（両方の時間から予約可能）
                    if start_time == 60:
                        start_minutes = [0, 30]
                        allows_thirty_minute_slots = True
                    else:
                        if start_time not in [0, 30]:
                            logger.warning(f"無効な開始時刻を検出: room_id={room_id}, start_time={start_time}")
                            start_minutes = [0]
                        else:
                            start_minutes = [start_time]
                        allows_thirty_minute_slots = False
                    
                    room_name = self.room_name_map.get(room_id)
                    if room_name:
                        self.start_minutes_map[room_name] = start_minutes
                        self.thirty_minute_slots_map[room_name] = allows_thirty_minute_slots
                        logger.debug(f"部屋 {room_name} の設定: start_minutes={start_minutes}, allows_thirty_minute_slots={allows_thirty_minute_slots}")
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"開始時刻の解析に失敗: room_id={room_id}, error={str(e)}")
                    room_name = self.room_name_map.get(room_id)
                    if room_name:
                        self.start_minutes_map[room_name] = [0]
                        self.thirty_minute_slots_map[room_name] = False

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
            response = self._make_request("POST", url, headers=headers, data=data)
            if not response.text.strip():
                raise StudioScraperError("スケジュールデータが空です")
            
            return response.json()
            
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
            # room_name_mapから実際の部屋名を取得
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
        
        for room_name, time_slots in studio_time_slots.items():
            merged_slots = self._merge_consecutive_slots(sorted(time_slots))
            # start_minutes_mapから開始時刻群を取得（デフォルトは[0]）
            start_minutes = self.start_minutes_map.get(room_name, [0])
            allows_thirty_minute_slots = self.thirty_minute_slots_map.get(room_name, False)
            
            studio_availabilities.append(
                StudioAvailability(
                    room_name=room_name,
                    time_slots=merged_slots,
                    date=target_date,
                    start_minutes=start_minutes,
                    allows_thirty_minute_slots=allows_thirty_minute_slots
                )
            )
            logger.debug(f"スタジオ {room_name} の利用可能枠: {len(merged_slots)}個")
        
        logger.info(f"予約可能時間の取得結果: {len(studio_availabilities)}件")
        # 結果をJSONとしてログに出力
        result_json = [
            {
                "room_name": avail.room_name,
                "date": avail.date.isoformat(),
                "time_slots": [
                    {
                        "start_time": slot.start_time.strftime("%H:%M"),
                        "end_time": slot.end_time.strftime("%H:%M")
                    }
                    for slot in avail.time_slots
                ],
                "start_minutes": avail.start_minutes,
                "allows_thirty_minute_slots": avail.allows_thirty_minute_slots
            }
            for avail in studio_availabilities
        ]
        logger.info(f"取得した予約可能時間: {json.dumps(result_json, indent=2, ensure_ascii=False)}")
        return studio_availabilities

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

    def _get_studio_info(self) -> requests.Response:
        """スタジオ情報を取得"""
        try:
            url = f"{self.BASE_URL}/studio/info/{self.shop_id}"
            logger.info(f"スタジオ情報の取得を開始: url={url}")
            
            response = self.session.get(url)
            response.raise_for_status()
            
            logger.debug(f"レスポンスステータス: {response.status_code}")
            logger.info("スタジオ情報の取得が完了")
            return response
            
        except requests.RequestException as e:
            error_msg = f"スタジオ情報の取得に失敗: url={url}, エラー: {str(e)}"
            logger.error(error_msg)
            raise StudioScraperError(error_msg) from e

def register(registry: ScraperRegistry) -> None:
    """Studiolスクレイパーの登録"""
    registry.register_strategy(
        'studiol',
        StudiolScraper,
        ScraperMetadata(
            description="Studiol予約システム用スクレイパー",
            version="1.0.0",
            requires_auth=False,
            base_url="https://studi-ol.com"
        )
    )
