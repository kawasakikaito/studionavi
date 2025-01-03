# scraper_padstudio.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
from .scraper_base import (
    StudioScraperStrategy,
    StudioScraperError,
    StudioTimeSlot,
    StudioAvailability
)
from scraper_register import ScraperRegistry, ScraperMetadata

class PadStudioScraper(StudioScraperStrategy):
    """padstudioの予約システムに対応するスクレイパー実装"""
    
    def __init__(self):
        """初期化処理"""
        self.base_url = "https://www.reserve1.jp/studio/member"
        self.session = requests.Session()

    def establish_connection(self, shop_id: Optional[str] = None) -> bool:
        """予約システムへの接続を確立し、セッションを初期化する"""
        url = f"{self.base_url}/VisitorLogin.php"
        params = self._prepare_connection_params()
        
        try:
            response = self._make_connection_request(url, params)
            return True
        except requests.RequestException as e:
            raise StudioScraperError(f"接続の確立に失敗しました: {str(e)}")

    def _prepare_connection_params(self) -> Dict:
        """接続用のパラメータを準備"""
        return {
            "lc": "olsccsvld",
            "mn": "3",
            "gr": "1"
        }

    def _make_connection_request(self, url: str, params: Dict) -> requests.Response:
        """接続リクエストを実行"""
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        if not response.text.strip():
            raise StudioScraperError("接続ページが空です")
            
        return response

    def fetch_available_times(self, date: str) -> List[StudioAvailability]:
        """指定された日付の予約可能時間を取得"""
        url = f"{self.base_url}/member_select.php"
        data = self._prepare_schedule_data(date)
        
        try:
            response = self._fetch_schedule_page(url, data)
            return self._parse_schedule_page(response.text, date)
        except requests.RequestException as e:
            raise StudioScraperError(f"スケジュールデータの取得に失敗しました: {str(e)}")

    def _prepare_schedule_data(self, date: str) -> Dict:
        """スケジュールリクエスト用のデータを準備"""
        ym = date[:7].replace("-", "")
        return {
            "grand": "1",
            "Ym_select": ym,
            "office": "1480320",  # 固定値
            "mngfg": "4",
            "rdate": date,
            "member_select": "3",
            "month_btn": "",
            "day_btn": date
        }

    def _fetch_schedule_page(self, url: str, data: Dict) -> requests.Response:
        """スケジュールページを取得"""
        response = self.session.post(url, data=data)
        response.raise_for_status()
        
        if not response.text.strip():
            raise StudioScraperError("スケジュールデータが空です")
            
        return response

    def _parse_schedule_page(self, html_content: str, date: str) -> List[StudioAvailability]:
        """スケジュールページをパースして利用可能時間を抽出"""
        soup = BeautifulSoup(html_content, 'html.parser')
        schedule_table = self._find_schedule_table(soup)
        
        if not schedule_table:
            return []

        time_slots = self._extract_time_slots(schedule_table)
        return self._extract_studio_availabilities(schedule_table, time_slots, date)

    def _find_schedule_table(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """スケジュールテーブルを検索"""
        form = soup.find('form', {'name': 'form1'})
        return form.find('table', {'class': 'table_base'}) if form else None

    def _extract_time_slots(self, schedule_table: BeautifulSoup) -> List[tuple]:
        """時間枠の情報を抽出"""
        time_slots = []
        first_row = schedule_table.find('tr')
        
        if first_row:
            time_cells = first_row.find_all('td', {'class': 'item_base'})
            for cell in time_cells:
                text = ' '.join(cell.stripped_strings)
                if text and '~' in text:
                    start_time, end_time = map(str.strip, text.split('~'))
                    time_slots.append((start_time, end_time))
                    
        return time_slots

    def _extract_studio_availabilities(
        self, 
        schedule_table: BeautifulSoup, 
        time_slots: List[tuple], 
        date: str
    ) -> List[StudioAvailability]:
        """スタジオごとの利用可能時間を抽出"""
        studio_availabilities = []
        studio_rows = schedule_table.find_all('tr')[1:]
        
        for row in studio_rows:
            studio_name = self._get_studio_name(row)
            if not studio_name:
                continue
                
            available_slots = self._get_available_slots(row, time_slots)
            if available_slots:
                studio_availabilities.append(
                    StudioAvailability(
                        room_name=studio_name,
                        time_slots=available_slots,
                        date=date
                    )
                )
                
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
        time_slots: List[tuple]
    ) -> List[StudioTimeSlot]:
        """行から利用可能な時間枠を取得"""
        available_slots = []
        cells = row.find_all('td')
        current_time_index = 0
        
        for cell in cells[1:-1]:
            colspan = int(cell.get('colspan', 1))
            
            if self._is_available_slot(cell) and current_time_index < len(time_slots):
                start_time, end_time = time_slots[current_time_index]
                available_slots.append(
                    StudioTimeSlot(
                        start_time=self._normalize_time(start_time),
                        end_time=self._normalize_time(end_time)
                    )
                )
            
            current_time_index += colspan
            
        return available_slots

    def _is_available_slot(self, cell: BeautifulSoup) -> bool:
        """セルが予約可能かどうかを判定"""
        return ('koma' in cell.get('class', []) and 
                'koma_03_x' not in cell.get('class', []) and 
                'koma_01_x' not in cell.get('class', []) and
                cell.find('input', {'type': 'checkbox', 'name': 'c_v[]'}))

    @staticmethod
    def _normalize_time(time_str: str) -> str:
        """時刻文字列を標準形式(HH:MM)に変換"""
        time_str = time_str.replace('：', ':')
        try:
            time_obj = datetime.strptime(time_str.strip(), '%H:%M')
            return time_obj.strftime('%H:%M')
        except ValueError:
            return time_str.strip()

def register(registry: ScraperRegistry) -> None:
    """PADスタジオスクレイパーの登録"""
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

def main():
    """使用例を示すメイン関数"""
    scraper = PadStudioScraper()
    try:
        # 接続確立
        scraper.establish_connection()
        
        # 空き状況の取得
        availabilities = scraper.fetch_available_times("2025-01-07")
        
        # 結果の出力
        print(scraper.to_json(availabilities))
        
    except StudioScraperError as e:
        print(f"エラーが発生しました: {e}")
        raise
    except Exception as e:
        print(f"予期せぬエラー: {e}")
        raise

if __name__ == "__main__":
    main()