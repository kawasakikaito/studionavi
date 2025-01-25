import requests
from bs4 import BeautifulSoup
from datetime import datetime, date, time
from typing import List, Dict, Optional, Tuple, Set
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

class PadStudioScraper(StudioScraperStrategy):
    """padstudioの予約システムに対応するスクレイパー実装"""
    
    def __init__(self):
        """初期化処理"""
        self.base_url: str = "https://www.reserve1.jp/studio/member"
        self.session: requests.Session = requests.Session()
        logger.debug("PadStudioScraperを初期化しました")

    def establish_connection(self, shop_id: Optional[str] = None) -> bool:
        """予約システムへの接続を確立し、セッションを初期化する
        
        Args:
            shop_id: スタジオの店舗ID（使用しないが、インターフェース互換性のため必要）
            
        Returns:
            bool: 接続が成功したかどうか
            
        Raises:
            StudioScraperError: 接続に失敗した場合
        """
        logger.info("予約システムへの接続を開始")
        url = f"{self.base_url}/VisitorLogin.php"
        params = self._prepare_connection_params()
        
        try:
            self._make_connection_request(url, params)
            logger.info("接続を確立しました")
            return True
        except requests.RequestException as e:
            logger.error(f"接続の確立に失敗: {str(e)}")
            raise StudioScraperError("接続の確立に失敗しました") from e

    def _prepare_connection_params(self) -> Dict[str, str]:
        """接続用のパラメータを準備"""
        logger.debug("接続パラメータを準備")
        return {
            "lc": "olsccsvld",
            "mn": "3",
            "gr": "1"
        }

    def _make_connection_request(self, url: str, params: Dict[str, str]) -> requests.Response:
        """接続リクエストを実行"""
        logger.debug(f"接続リクエストを実行: url={url}")
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        if not response.text.strip():
            logger.error("接続ページが空です")
            raise StudioScraperError("接続ページが空です")
            
        return response

    def fetch_available_times(self, target_date: date) -> List[StudioAvailability]:
        """指定された日付の予約可能時間を取得
        
        PAD Studioは常に00分スタートのスタジオのみをサポートしているため、
        start_minutesは常に[0]となります。
        
        Args:
            target_date: 対象日付
            
        Returns:
            List[StudioAvailability]: 予約可能時間のリスト
            
        Raises:
            StudioScraperError: スケジュールデータの取得に失敗した場合
        """
        logger.info(f"予約可能時間の取得を開始: date={target_date}")
        url = f"{self.base_url}/member_select.php"
        data = self._prepare_schedule_data(target_date)
        
        try:
            response = self._fetch_schedule_page(url, data)
            result = self._parse_schedule_page(response.text, target_date)
            logger.info(f"予約可能時間の取得が完了: {len(result)}件")
            return result
        except requests.RequestException as e:
            logger.error(f"スケジュールデータの取得に失敗: {str(e)}")
            raise StudioScraperError("スケジュールデータの取得に失敗しました") from e

    def _prepare_schedule_data(self, target_date: date) -> Dict[str, str]:
        """スケジュールリクエスト用のデータを準備"""
        logger.debug(f"スケジュールデータを準備: date={target_date}")
        return {
            "grand": "1",
            "Ym_select": target_date.strftime("%Y%m"),
            "office": "1480320",  # 固定値
            "mngfg": "4",
            "rdate": target_date.isoformat(),
            "member_select": "3",
            "month_btn": "",
            "day_btn": target_date.isoformat()
        }

    def _fetch_schedule_page(self, url: str, data: Dict[str, str]) -> requests.Response:
        """スケジュールページを取得"""
        logger.debug("スケジュールページの取得を開始")
        response = self.session.post(url, data=data)
        response.raise_for_status()
        
        if not response.text.strip():
            logger.error("スケジュールデータが空です")
            raise StudioScraperError("スケジュールデータが空です")
        
        logger.debug("スケジュールページの取得が完了")
        return response

    def _parse_schedule_page(
        self,
        html_content: str,
        target_date: date
    ) -> List[StudioAvailability]:
        """スケジュールページをパースして利用可能時間を抽出"""
        logger.debug("スケジュールページのパースを開始")
        soup = BeautifulSoup(html_content, 'html.parser')
        schedule_table = self._find_schedule_table(soup)
        
        if not schedule_table:
            logger.warning("スケジュールテーブルが見つかりません")
            return []

        time_slots = self._extract_time_slots(schedule_table)
        result = self._extract_studio_availabilities(schedule_table, time_slots, target_date)
        logger.debug(f"スケジュールページのパースが完了: {len(result)}件のスタジオ情報")
        return result

    def _find_schedule_table(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """スケジュールテーブルを検索"""
        logger.debug("スケジュールテーブルの検索を開始")
        form = soup.find('form', {'name': 'form1'})
        if not form:
            logger.warning("予約フォームが見つかりません")
            return None
        return form.find('table', {'class': 'table_base'})

    def _extract_time_slots(self, schedule_table: BeautifulSoup) -> List[Tuple[time, time]]:
        """時間枠の情報を抽出"""
        logger.debug("時間枠の抽出を開始")
        time_slots: List[Tuple[time, time]] = []
        first_row = schedule_table.find('tr')
        
        if first_row:
            time_cells = first_row.find_all('td', {'class': 'item_base'})
            logger.debug(f"時間セル数: {len(time_cells)}")
            
            for cell in time_cells:
                text = ' '.join(cell.stripped_strings)
                if text and '~' in text:
                    start_str, end_str = map(str.strip, text.split('~'))
                    try:
                        start_time = self._parse_time(start_str)
                        end_time = self._parse_time(end_str)
                        if start_time and end_time:
                            time_slots.append((start_time, end_time))
                    except ValueError:
                        logger.warning(f"時間のパースに失敗: {text}")
                        continue
                    
        logger.debug(f"抽出された時間枠: {len(time_slots)}個")
        return time_slots

    def _extract_studio_availabilities(
        self,
        schedule_table: BeautifulSoup,
        time_slots: List[Tuple[time, time]],
        target_date: date
    ) -> List[StudioAvailability]:
        """スタジオごとの利用可能時間を抽出"""
        studio_availabilities: List[StudioAvailability] = []
        studio_rows = schedule_table.find_all('tr')[1:]  # ヘッダー行をスキップ
        logger.debug(f"スタジオ行数: {len(studio_rows)}")
        
        for row in studio_rows:
            studio_name = self._get_studio_name(row)
            if not studio_name:
                logger.warning("スタジオ名の取得に失敗しました")
                continue
                
            available_slots = self._get_available_slots(row, time_slots)
            if available_slots:
                # PAD Studioは常に00分スタート、30分単位予約は不可
                studio_availabilities.append(
                    StudioAvailability(
                        room_name=studio_name,
                        date=target_date,
                        time_slots=available_slots,
                        start_minutes=[0],  # 常に[0]（00分スタート）
                        allows_thirty_minute_slots=False  # 常にFalse
                    )
                )
                logger.debug(f"スタジオ {studio_name} の利用可能枠: {len(available_slots)}個")
                
        return studio_availabilities

    def _get_studio_name(self, row: BeautifulSoup) -> Optional[str]:
        """行からスタジオ名を取得"""
        cells = row.find_all('td')
        if not cells:
            return None
        return cells[0].get_text(strip=True)

    def _get_available_slots(
        self,
        row: BeautifulSoup,
        time_slots: List[Tuple[time, time]]
    ) -> List[StudioTimeSlot]:
        """行から利用可能な時間枠を取得"""
        available_slots: List[StudioTimeSlot] = []
        cells = row.find_all('td')
        current_time_index = 0
        
        # 連続した時間枠を追跡するための変数
        current_start_index = None
        current_end_index = None
        
        for cell_index, cell in enumerate(cells[1:-1]):  # 最初の列（部屋名）と最後の列をスキップ
            colspan = int(cell.get('colspan', 1))
            
            if self._is_available_slot(cell):
                if current_start_index is None:
                    current_start_index = current_time_index
                current_end_index = current_time_index + colspan
            else:
                # 利用不可能なセルが見つかったら、それまでの連続した時間枠を追加
                if current_start_index is not None:
                    start_time = time_slots[current_start_index][0]
                    end_time = time_slots[current_end_index - 1][1]
                    available_slots.append(
                        StudioTimeSlot(
                            start_time=start_time,
                            end_time=end_time
                        )
                    )
                    current_start_index = None
                
            current_time_index += colspan
        
        # 最後の連続した時間枠を追加
        if current_start_index is not None:
            start_time = time_slots[current_start_index][0]
            end_time = time_slots[current_end_index - 1][1]
            available_slots.append(
                StudioTimeSlot(
                    start_time=start_time,
                    end_time=end_time
                )
            )
        
        return available_slots

    def _is_available_slot(self, cell: BeautifulSoup) -> bool:
        """セルが予約可能かどうかを判定"""
        return ('koma' in cell.get('class', []) and 
                'koma_03_x' not in cell.get('class', []) and 
                'koma_01_x' not in cell.get('class', []) and
                cell.find('input', {'type': 'checkbox', 'name': 'c_v[]'}) is not None)

    @staticmethod
    def _parse_time(time_str: str) -> Optional[time]:
        """時刻文字列をtime型に変換"""
        time_str = time_str.replace('：', ':').strip()
        try:
            dt = datetime.strptime(time_str, '%H:%M')
            return dt.time()
        except ValueError:
            return None

def register(registry: ScraperRegistry) -> None:
    """PADスタジオスクレイパーの登録"""
    logger.info("PADスタジオスクレイパーの登録を開始")
    registry.register_strategy(
        'pad_studio',
        PadStudioScraper,
        ScraperMetadata(
            description="PADスタジオ予約システム用スクレイパー",
            version="1.0.0",
            requires_auth=True,
            base_url="https://www.reserve1.jp"
        )
    )
    logger.info("PADスタジオスクレイパーの登録が完了")