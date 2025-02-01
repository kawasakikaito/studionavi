from typing import List, Optional, Dict, Tuple
import requests
import re
import json
import traceback
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

class Studio246Room:
    """Studio246の各部屋の情報を保持するクラス"""
    def __init__(self, room_name: str, start_minutes: int):
        self.room_name = room_name
        self.start_minutes = start_minutes
        self.time_slots: List[Dict[str, any]] = []

    def add_time_slot(self, start_time: time, end_time: time, state: str, classes: List[str]):
        """時間枠を追加
        
        Args:
            start_time: 開始時間
            end_time: 終了時間
            state: セルの状態（past, full等）
            classes: セルのクラス名リスト
        """
        self.time_slots.append({
            "start": start_time,
            "end": end_time,
            "state": state,
            "classes": classes
        })

    def get_available_time_slots(self) -> List[Dict[str, any]]:
        """予約可能な時間枠のみを返す"""
        return [
            {
                "start": slot["start"],
                "end": slot["end"],
                "available": True
            }
            for slot in self.time_slots
            if self._is_available(slot)
        ]

    def _is_available(self, time_slot: Dict[str, any]) -> bool:
        """時間枠が予約可能かどうかを判定"""
        # bg-blackクラスがある場合は予約不可
        if 'bg_black' in time_slot['classes']:
            return False
            
        # pastまたはfull状態は予約不可
        if time_slot['state'] in ['past', 'full']:
            return False
            
        return True

class Studio246Scraper(StudioScraperStrategy):
    """Studio246の予約システムに対応するスクレイパー実装"""
    
    BASE_URL = "https://www.studio246.net/reserve/"
    AJAX_URL = "https://www.studio246.net/reserve/ajax/ajax_timeline_contents.php"
    MAX_RETRIES = 5
    MIN_WAIT = 3
    MAX_WAIT = 15
    TIME_SLOT_DURATION = 3600  # 1時間（秒）
    
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
        
        # 各スタジオの開始時刻を設定
        for i in range(1, 5):  # スタジオ1から4まで
            self.start_minutes_map[str(i)] = [0, 15, 30, 45]  # 15分単位で予約可能
            self.thirty_minute_slots_map[str(i)] = True  # 30分単位での予約を許可

    def fetch_available_times(self, target_date: date) -> List[StudioAvailability]:
        """指定された日付の予約可能時間を取得
        
        Args:
            target_date: 対象日付
            
        Returns:
            List[StudioAvailability]: 予約可能時間のリスト
            
        Raises:
            StudioScraperError: スケジュールデータの取得に失敗した場合
        """
        logger.info(f"=== 予約可能時間の取得を開始 - 対象日: {target_date} ===")
        logger.debug(f"処理開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # スケジュールデータを取得
            schedule_data = self._fetch_schedule_data(target_date)
            logger.debug(f"取得したスケジュールデータ:")
            for item in schedule_data:
                logger.debug(f"  - {json.dumps(item, ensure_ascii=False, indent=2)}")

            # 各部屋の空き状況を解析
            availabilities = []
            logger.debug("=== 部屋ごとの空き状況解析開始 ===")
            for studio_data in schedule_data:
                room_name = studio_data.get("room_name", "")
                logger.debug(f"\n--- スタジオ {room_name} の解析開始 ---")
                time_slots = []
                
                # 利用可能な時間枠を処理
                logger.debug(f"タイムライン数: {len(studio_data.get('timeline', []))}")
                for slot in studio_data.get("timeline", []):
                    try:
                        logger.debug(f"\n時間枠データ: {json.dumps(slot, ensure_ascii=False, indent=2)}")
                        start_time = slot["start"]
                        end_time = slot["end"]
                        logger.debug(f"解析された時間 - 開始: {start_time}, 終了: {end_time}")
                        
                        if slot.get("available", False):
                            time_slot = StudioTimeSlot(
                                start_time=start_time,
                                end_time=end_time
                            )
                            time_slots.append(time_slot)
                            logger.debug(f"利用可能な時間枠を追加: {time_slot}")
                        else:
                            logger.debug("この時間枠は利用不可")
                    except (ValueError, KeyError) as e:
                        logger.warning(f"時間枠の解析に失敗: {str(e)}")
                        logger.debug(f"エラー詳細:\n{traceback.format_exc()}")
                        continue

                # 時間枠が存在する場合のみ追加
                if time_slots:
                    logger.debug(f"\nスタジオ {room_name} の利用可能時間枠:")
                    for ts in time_slots:
                        logger.debug(f"  {ts.start_time} - {ts.end_time}")
                    
                    # 246スタジオは15分単位で予約可能
                    availability = StudioAvailability(
                        room_name=room_name,
                        date=target_date,
                        time_slots=time_slots,
                        start_minutes=[0, 15, 30, 45],  # 15分単位で予約可能
                        allows_thirty_minute_slots=True  # 30分単位での予約を許可
                    )
                    availabilities.append(availability)
                    logger.debug(f"スタジオ {room_name} の利用可能情報を追加完了")
                else:
                    logger.debug(f"スタジオ {room_name} の利用可能時間枠なし")

            logger.info(f"=== 予約可能時間の取得が完了 - 件数: {len(availabilities)} ===")
            logger.debug("取得された予約可能時間の詳細:")
            for avail in availabilities:
                logger.debug(f"\nスタジオ: {avail.room_name}")
                logger.debug(f"日付: {avail.date}")
                logger.debug("時間枠:")
                for ts in avail.time_slots:
                    logger.debug(f"  {ts.start_time} - {ts.end_time}")
            return availabilities

        except Exception as e:
            error_msg = f"スケジュールデータの取得に失敗: date={target_date}, エラー: {str(e)}"
            logger.error(error_msg)
            logger.error(f"エラー詳細:\n{traceback.format_exc()}")
            raise StudioScraperError(error_msg) from e

    def _fetch_schedule_data(self, target_date: date) -> List[Dict]:
        """APIから生のスケジュールデータを取得"""
        try:
            headers, data = self._prepare_schedule_request(target_date)
            logger.debug(f"スケジュールリクエストヘッダー: {headers}")
            logger.debug(f"スケジュールリクエストデータ: {data}")
            
            response = requests.post(self.AJAX_URL, headers=headers, data=data)
            logger.debug(f"スケジュールレスポンスステータス: {response.status_code}")
            logger.debug(f"スケジュールレスポンスヘッダー: {response.headers}")
            logger.debug(f"スケジュールレスポンス本文: {response.text[:500]}")  # 最初の500文字のみ表示
            
            # レスポンスを一時的にファイルに保存
            with open('/tmp/studio246_response.html', 'w') as f:
                f.write(response.text)
            logger.debug("レスポンスを /tmp/studio246_response.html に保存しました")
            
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

    def _parse_schedule_html(self, html_content: str, target_date: date) -> List[Dict]:
        """HTMLコンテンツを解析してスケジュールデータを取得"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 部屋情報の初期化
        rooms: Dict[str, Studio246Room] = {}
        
        # timeline_headerから部屋情報を取得
        timeline_header = soup.find('tr', class_='timeline_header')
        if not timeline_header:
            raise StudioScraperError("タイムラインヘッダーが見つかりません")

        # timeline_headerのtd要素から開始時間を取得
        time_cells = timeline_header.find_all('td')
        start_minutes = []
        for cell in time_cells:
            text = cell.get_text(strip=True)
            if text and '分' in text:
                try:
                    minute = int(text.replace('分', ''))
                    start_minutes.append(minute)
                except ValueError:
                    logger.warning(f"開始時間の解析に失敗: {text}")
            
        # 各部屋の情報を取得
        for i, cell in enumerate(timeline_header.find_all('th')[1:]):  # 最初のthはラベルなのでスキップ
            room_name = cell.get_text(strip=True)
            if room_name and i < len(start_minutes):
                rooms[str(i)] = Studio246Room(room_name, start_minutes[i])

        # タイムラインの各行を処理
        for row in soup.find_all('tr'):
            # 時間セルを取得
            time_cell = row.find('td', class_='time_hidden')
            if not time_cell:
                continue
                
            time_str = time_cell.get('data-time')
            if not time_str:
                continue
                
            # 時間を解析
            try:
                hour, minute = map(int, time_str.split(':'))
                current_time = time(hour=hour, minute=minute)
                
                # 終了時間は1時間後
                end_hour = (hour + 1) % 24
                end_time = time(hour=end_hour, minute=minute)
                
                # 各部屋のセルを処理
                cells = row.find_all('td')[1:]  # 最初のtdは時間なのでスキップ
                for i, cell in enumerate(cells):
                    room_key = str(i)
                    if room_key in rooms:
                        # セルの状態とクラスを取得
                        state = cell.get('state', '')
                        classes = cell.get('class', [])
                        
                        # すべての情報を保持
                        rooms[room_key].add_time_slot(current_time, end_time, state, classes)
                
            except ValueError:
                logger.warning(f"時間の解析に失敗: {time_str}")
                continue

        # 結果を整形（StudioAvailabilityの形式に変換）
        result = []
        for room in rooms.values():
            # 予約可能な時間枠を取得
            available_slots = room.get_available_time_slots()
            
            # StudioTimeSlotオブジェクトに変換
            time_slots = []
            for slot in available_slots:
                time_slots.append(
                    StudioTimeSlot(
                        start_time=slot["start"],
                        end_time=slot["end"]
                    )
                )
            
            # StudioAvailabilityオブジェクトを作成
            availability = StudioAvailability(
                room_name=room.room_name,
                date=target_date,
                time_slots=time_slots,
                start_minutes=[room.start_minutes],  # その部屋の開始時間
                allows_thirty_minute_slots=False  # Studio246は30分単位での予約を許可しない
            )
            result.append(availability)
            
        return result

    def _prepare_schedule_request(self, target_date: date) -> tuple:
        """スケジュールリクエストのヘッダーとデータを準備"""
        if not self._token or not self.shop_id:
            raise StudioScraperError("接続が確立されていません")
            
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

