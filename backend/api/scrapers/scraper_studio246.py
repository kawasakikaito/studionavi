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

class Studio246Scraper(StudioScraperStrategy):
    """Studio246の予約システムに対応するスクレイパー実装"""
    
    BASE_URL = "https://www.studio246.net/reserve/"
    AJAX_URL = "https://www.studio246.net/reserve/ajax/ajax_timeline_contents.php"
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

    def establish_connection(self, shop_id: str) -> bool:
        """予約システムへの接続を確立し、トークンを取得する"""
        try:
            token = self._fetch_token(shop_id)
            self._set_connection_info(shop_id, token)
            logger.info(f"接続を確立しました: shop_id={shop_id}")
            return True
            
        except StudioScraperError:
            raise
        except Exception as e:
            logger.error(f"接続の確立に失敗: {str(e)}")
            raise StudioScraperError("接続の確立に失敗しました") from e

    def _fetch_token(self, shop_id: str) -> str:
        """ページからPHPSESSIDを取得"""
        try:
            url = f"{self.BASE_URL}?si={shop_id}"
            logger.debug(f"セッション取得リクエストURL: {url}")
            
            # 初回リクエストでPHPSESSIDを取得
            response = requests.get(url)
            response.raise_for_status()
            
            # Cookieからセッションを取得
            cookies = response.cookies
            phpsessid = cookies.get('PHPSESSID')
            
            if not phpsessid:
                # レスポンスヘッダーからも確認
                cookie_header = response.headers.get('Set-Cookie', '')
                match = re.search(r'PHPSESSID=([^;]+)', cookie_header)
                if match:
                    phpsessid = match.group(1)
            
            logger.debug(f"取得したPHPSESSID: {phpsessid}")
            
            if not phpsessid:
                raise StudioScraperError("セッションIDの取得に失敗しました")
                
            return phpsessid
            
        except requests.RequestException as e:
            logger.error(f"セッション取得リクエストに失敗: {str(e)}")
            raise StudioScraperError("セッション取得リクエストに失敗しました") from e

    def _set_connection_info(self, shop_id: str, token: str) -> None:
        """接続情報を設定"""
        self.shop_id = shop_id
        self._token = token

    def fetch_available_times(self, target_date: date) -> List[StudioAvailability]:
        """指定された日付の予約可能時間を取得"""
        try:
            schedule_data = self._fetch_raw_schedule_data(target_date)
            studio_time_slots = self._group_time_slots_by_studio(schedule_data)
            return self._create_studio_availabilities(studio_time_slots, target_date)
            
        except StudioScraperError:
            raise
        except Exception as e:
            logger.error(f"予約可能時間の取得に失敗: {str(e)}")
            raise StudioScraperError("予約可能時間の取得に失敗しました") from e

    def _fetch_raw_schedule_data(self, target_date: date) -> List[dict]:
        """APIから生のスケジュールデータを取得"""
        try:
            headers, data = self._prepare_schedule_request(target_date)
            logger.debug(f"スケジュールリクエストヘッダー: {headers}")
            logger.debug(f"スケジュールリクエストデータ: {data}")
            
            response = requests.post(self.AJAX_URL, headers=headers, data=data)
            logger.debug(f"スケジュールレスポンスステータス: {response.status_code}")
            logger.debug(f"スケジュールレスポンスヘッダー: {response.headers}")
            logger.debug(f"スケジュールレスポンス本文: {response.text[:50000]}")  # 最初の500文字のみ表示
            
            response.raise_for_status()
            
            # HTMLレスポンスをパース
            schedule_data = self._parse_schedule_html(response.text, target_date)
            if not schedule_data:
                logger.warning("スケジュールデータが空です")
                return []
                
            return schedule_data
            
        except requests.RequestException as e:
            logger.error(f"スケジュールデータの取得に失敗: {str(e)}")
            raise StudioScraperError("スケジュールデータの取得に失敗しました") from e
        except Exception as e:
            logger.error(f"スケジュールデータの解析に失敗: {str(e)}")
            raise StudioScraperError("スケジュールデータの解析に失敗しました") from e

    def _parse_schedule_html(self, html_content: str, target_date: date) -> List[dict]:
        """HTMLレスポンスからスケジュール情報を抽出"""
        schedule_data = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # タイムラインブロックを取得
        timeline_blocks = soup.find_all('div', class_='timeline_block')
        if not timeline_blocks:
            logger.warning("タイムラインブロックが見つかりません")
            return []
        
        # 指定された日付のタイムラインブロックを探す
        target_block = None
        for block in timeline_blocks:
            block_date_str = block.get('data-date')
            if not block_date_str:
                continue
                
            try:
                block_date = datetime.strptime(block_date_str, '%Y-%m-%d').date()
                if block_date == target_date:
                    target_block = block
                    break
            except ValueError:
                logger.warning(f"不正な日付形式: {block_date_str}")
                continue
        
        if not target_block:
            logger.warning(f"対象日付 {target_date} のタイムラインブロックが見つかりません")
            return []
            
        logger.debug(f"タイムラインブロックの日付: {target_date}")
        
        # テーブル内の予約可能な時間枠を処理
        time_cells = target_block.find_all('td')
        logger.debug(f"見つかったセルの総数: {len(time_cells)}")
        
        for cell in time_cells:
            try:
                # 予約可能な時間枠の条件をチェック
                cell_classes = cell.get('class', [])
                cell_state = cell.get('state')
                
                if not (
                    'time_cell' in cell_classes and  # time_cellクラスを持っている
                    'bg_black' not in cell_classes and  # bg_blackクラスを持っていない
                    cell_state == 'posi'  # stateがposi
                ):
                    continue

                # 時刻を取得
                time_str = cell.get('data-time')
                if not time_str:
                    continue

                logger.debug(f"予約可能な時間枠を検出: {time_str}, クラス: {cell_classes}, 状態: {cell_state}")

                try:
                    # 時刻のパース
                    hour = int(time_str.split(':')[0])
                    minute = int(time_str.split(':')[1])

                    # 24:00以降の時間は次の日の予約として扱う
                    slot_date = target_date
                    if hour >= 24:
                        hour -= 24
                        slot_date += timedelta(days=1)
                        logger.debug(f"24時以降の時間枠を検出: {time_str} -> {hour:02d}:{minute:02d} (翌日の予約)")

                    # 時刻を標準形式に変換
                    time_str = f"{hour:02d}:{minute:02d}"
                    start_time = datetime.combine(
                        slot_date,
                        datetime.strptime(time_str, '%H:%M').time()
                    )

                    schedule_item = {
                        'studio_id': '1',  # スタジオIDは固定値として設定
                        'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'is_available': True
                    }
                    schedule_data.append(schedule_item)
                    logger.debug(f"予約可能時間を追加: {schedule_item}")

                except ValueError as e:
                    logger.error(f"時刻のパースに失敗: {time_str}, エラー: {str(e)}")
                    continue

            except Exception as e:
                logger.error(f"時間枠の解析に失敗: {str(e)}")
                continue

        logger.debug(f"パースされたスケジュールデータ: {len(schedule_data)}件")
        if not schedule_data:
            logger.warning(f"予約可能な時間枠が見つかりませんでした（対象日: {target_date}）")
        return schedule_data

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

    def _group_time_slots_by_studio(self, schedule_data: List[dict]) -> Dict[str, List[datetime]]:
        """スタジオごとに時間枠をグループ化"""
        studio_time_slots: Dict[str, List[datetime]] = {}
        
        for item in schedule_data:
            studio_id = str(item.get('studio_id', ''))
            start_time_str = item.get('start_time', '')
            is_available = item.get('is_available', False)
            
            if not all([studio_id, start_time_str, is_available]):
                continue
                
            try:
                # 時間枠を独立して扱う
                start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
                minute = start_time.minute
                
                # 開始時刻（分）に基づいてスタジオIDを設定
                studio_id = str(minute)  # 0, 15, 30, 45分の部屋に対応
                
                if studio_id not in studio_time_slots:
                    studio_time_slots[studio_id] = []
                studio_time_slots[studio_id].append(start_time)
                logger.debug(f"時間枠を追加: studio_id={studio_id}, start_time={start_time}")
                
            except ValueError as e:
                logger.error(f"日時のパースに失敗: {str(e)}")
                continue
                
        return studio_time_slots

    def _create_studio_availabilities(
        self,
        studio_time_slots: Dict[str, List[datetime]],
        target_date: date
    ) -> List[StudioAvailability]:
        """スタジオごとの利用可能時間を作成"""
        availabilities = []
        
        # 開始時刻（分）ごとの時間枠を格納
        slots_by_minute = {
            0: [],   # 00分スタート
            15: [],  # 15分スタート
            30: [],  # 30分スタート
            45: []   # 45分スタート
        }
        
        for studio_id, time_slots in studio_time_slots.items():
            if not time_slots:
                continue
                
            # 時間枠を開始時刻（分）ごとに分類
            for dt in time_slots:
                minute = dt.minute
                if minute in slots_by_minute:
                    slots_by_minute[minute].append(dt)
        
        # 各開始時刻（分）ごとに利用可能時間を作成
        for minute, slots in slots_by_minute.items():
            if not slots:
                continue
                
            # 時間枠をソート
            sorted_slots = sorted(set(slots))  # 重複を排除
            time_slot_objects = []
            
            # 各時間枠を独立して処理
            for slot in sorted_slots:
                # 1時間の時間枠を作成
                end_time = slot + timedelta(hours=1)
                
                # datetimeからtimeオブジェクトを作成
                start_time_obj = time(slot.hour, slot.minute)
                end_time_obj = time(end_time.hour % 24, end_time.minute)
                
                time_slot = StudioTimeSlot(
                    start_time=start_time_obj,
                    end_time=end_time_obj
                )
                time_slot_objects.append(time_slot)
            
            # 時間枠が見つかった場合のみ、利用可能時間を作成
            if time_slot_objects:
                room_name = f"Room {minute}"  # 部屋名は仮の値
                availability = StudioAvailability(
                    room_name=room_name,
                    date=target_date,
                    time_slots=time_slot_objects,
                    start_minutes=[minute],  # その開始時刻のみを許可
                    allows_thirty_minute_slots=False,  # Studio246は30分枠を許可しない
                    valid_start_minutes={0, 15, 30, 45}  # 各部屋の開始時刻に対応
                )
                availabilities.append(availability)
                
        return availabilities

    def _merge_consecutive_slots(self, time_slots: List[datetime]) -> List[Tuple[datetime, datetime]]:
        """連続する時間枠をマージ"""
        if not time_slots:
            return []
            
        # 時間枠をソート
        sorted_slots = sorted(time_slots)
        merged = []
        current_start = sorted_slots[0]
        current_end = current_start + timedelta(hours=1)
        
        for slot in sorted_slots[1:]:
            # 次の時間枠の開始時刻
            next_start = slot
            next_end = slot + timedelta(hours=1)
            
            # 現在の時間枠と次の時間枠が連続している場合
            if next_start == current_end:
                # 時間枠をマージ
                current_end = next_end
            else:
                # 連続していない場合は新しい時間枠を追加
                merged.append((current_start, current_end))
                current_start = next_start
                current_end = next_end
        
        # 最後の時間枠を追加
        merged.append((current_start, current_end))
        return merged

    def _create_time_slot(self, start: datetime, end: datetime) -> Optional[StudioTimeSlot]:
        """時間枠オブジェクトを作成"""
        if not start or not end:
            return None
            
        # 終了時刻を1時間後に設定
        end = start + timedelta(hours=1)
        
        # datetimeからtimeオブジェクトを作成
        start_time = time(start.hour, start.minute)
        end_time = time(end.hour % 24, end.minute)
        
        return StudioTimeSlot(
            start_time=start_time,
            end_time=end_time
        )

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