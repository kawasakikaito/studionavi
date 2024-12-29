from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re

class StudioAnalyzer:
    @staticmethod
    def parse_datetime(dt_str):
        return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')

    @staticmethod
    def format_time(dt):
        return dt.strftime('%H:%M')

    @staticmethod
    def parse_search_time(time_str):
        return datetime.strptime(time_str, '%H:%M').time()

    def extract_available_slots(self, html_content):
        """HTMLから予約可能な時間枠を抽出"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 日付を取得
        date_str = None
        caption = soup.find('caption', class_='item_05')
        if caption:
            date_match = re.search(r'(\d{4})年(\d{2})月(\d{2})日', caption.text)
            if date_match:
                year, month, day = date_match.groups()
                date_str = f"{year}-{month}-{day}"

        # 時間枠の取得
        time_slots = []
        table = soup.find('table', class_='table_base')
        if table:
            # 時間帯の取得
            time_headers = table.find_all('td', class_='item_base')[1:-1]
            time_ranges = []
            for header in time_headers:
                times = header.text.strip().split('~')
                if len(times) == 2:
                    # 全角文字を半角に変換
                    start_time = times[0].strip().replace('：', ':')
                    end_time = times[1].strip().replace('：', ':')
                    time_ranges.append((start_time, end_time))

            # スタジオごとの予約状況を取得
            for row in table.find_all('tr')[1:]:
                cells = row.find_all('td')
                if len(cells) < 3:
                    continue
                
                studio_name = cells[0].text.strip()
                for i, cell in enumerate(cells[1:-1]):
                    if cell.find('input', type='checkbox'):
                        if i < len(time_ranges):
                            start_time = f"{date_str} {time_ranges[i][0]}:00"
                            time_slots.append({
                                'roomId': studio_name,
                                'start': start_time,
                                'pInd': 0
                            })

        return time_slots

    def analyze_schedule(self, data, date_str, duration_hours, range_start="09:00", range_end="23:00"):
        """指定された条件で利用可能な部屋と時間枠を分析"""
        # 予約データを部屋ごとに整理
        rooms = {}
        for slot in sorted(data, key=lambda x: (x['roomId'], x['start'])):
            room_id = slot['roomId']
            start_time = self.parse_datetime(slot['start'])
            
            if room_id not in rooms:
                rooms[room_id] = []
            
            rooms[room_id].append({
                'start': start_time,
                'end': start_time + timedelta(hours=1),  # 1時間単位
                'price': slot['pInd']
            })

        # 条件に合う空き時間を検索
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        available_rooms = []

        for room_id, slots in rooms.items():
            available_ranges = self._find_available_ranges(
                slots, duration_hours, range_start, range_end)
            
            if available_ranges:
                time_ranges = [
                    f"{self.format_time(time_range['start'])}～{self.format_time(time_range['end'])}"
                    for time_range in available_ranges
                ]
                available_rooms.append((room_id, time_ranges))

        return available_rooms

    def _find_available_ranges(self, slots, duration_hours, range_start, range_end):
        """連続した利用可能時間帯を探索"""
        if not slots:
            return []

        range_start_time = self.parse_search_time(range_start)
        range_end_time = self.parse_search_time(range_end)
        available_ranges = []
        
        sorted_slots = sorted(slots, key=lambda x: x['start'])
        
        i = 0
        while i < len(sorted_slots):
            start_slot = sorted_slots[i]
            start_time = start_slot['start']
            
            if start_time.time() < range_start_time:
                i += 1
                continue
                
            # 連続する時間枠を探索
            consecutive_time = timedelta(hours=0)
            current_time = start_time
            consecutive_slots = []
            
            while i < len(sorted_slots) and consecutive_time < timedelta(hours=duration_hours):
                slot = sorted_slots[i]
                if slot['start'] != current_time or current_time.time() > range_end_time:
                    break
                    
                consecutive_time += timedelta(hours=1)
                consecutive_slots.append(slot)
                current_time += timedelta(hours=1)
                i += 1
            
            if consecutive_time >= timedelta(hours=duration_hours):
                end_time = start_time + consecutive_time
                if end_time.time() <= range_end_time:
                    available_ranges.append({
                        'start': start_time,
                        'end': end_time
                    })
            else:
                i += 1
        
        return available_ranges

# 使用例
def analyze_studio_schedule(html_content, duration_hours, range_start, range_end):
    analyzer = StudioAnalyzer()
    slots = analyzer.extract_available_slots(html_content)
    
    if slots:
        date_str = datetime.strptime(slots[0]['start'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
        return analyzer.analyze_schedule(slots, date_str, duration_hours, range_start, range_end)
    return []