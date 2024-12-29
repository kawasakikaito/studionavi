from datetime import datetime, timedelta

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

    def analyze_schedule(self, data, date_str, duration_hours, range_start, range_end):
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
                'end': start_time + timedelta(minutes=30),
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
        needed_slots = duration_hours * 2
        available_ranges = []
        
        sorted_slots = sorted(slots, key=lambda x: x['start'])
        
        i = 0
        while i <= len(sorted_slots) - needed_slots:
            start_slot = sorted_slots[i]
            start_time = start_slot['start']
            
            if start_time.time() < range_start_time:
                i += 1
                continue
            
            consecutive_slots = 1
            check_time = start_time + timedelta(minutes=30)
            
            for j in range(i + 1, len(sorted_slots)):
                if sorted_slots[j]['start'] != check_time:
                    break
                    
                if check_time.time() > range_end_time:
                    break
                    
                consecutive_slots += 1
                check_time += timedelta(minutes=30)
            
            if consecutive_slots >= needed_slots:
                end_time = start_time + timedelta(minutes=30 * consecutive_slots)
                if end_time.time() <= range_end_time:
                    available_ranges.append({
                        'start': start_time,
                        'end': end_time
                    })
            
            i += 1
        
        return available_ranges