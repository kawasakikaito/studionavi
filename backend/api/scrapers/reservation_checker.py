# reservation_checker.py
from typing import List, Optional, Dict
from datetime import time, datetime, date, timedelta
from dataclasses import dataclass
from scraper_base import (
    StudioTimeSlot,
    StudioAvailability,
    StudioValidationError
)

@dataclass
class TimeRange:
    """時間範囲を表すデータクラス"""
    start: time
    end: time

    def __post_init__(self) -> None:
        """初期化後の検証"""
        self.validate_time_order(self.start, self.end)

    @classmethod
    def from_datetime(cls, dt: datetime) -> 'TimeRange':
        """datetimeオブジェクトからTimeRangeを作成"""
        return cls(dt.time(), dt.time())

    @staticmethod
    def validate_time_order(start: time, end: time) -> None:
        """開始時刻が終了時刻より前であることを検証"""
        start_minutes = start.hour * 60 + start.minute
        end_minutes = end.hour * 60 + end.minute
        
        if end_minutes == 0:
            end_minutes = 24 * 60
            
        if start_minutes >= end_minutes:
            raise StudioValidationError(
                f"開始時刻({start.strftime('%H:%M')})は"
                f"終了時刻({end.strftime('%H:%M')})より前である必要があります"
            )

class AvailabilityChecker:
    """予約可能時間をチェックするクラス"""

    def __init__(self, availabilities: List[StudioAvailability]):
        self.availabilities = availabilities
        # 時間調整の管理用のマップ
        self._time_adjustments: Dict[str, bool] = {}
        for availability in availabilities:
            self._time_adjustments[availability.room_name] = availability.starts_at_thirty

    def _combine_date_time(self, d: date, t: time) -> datetime:
        """日付と時刻を組み合わせてdatetimeオブジェクトを作成"""
        return datetime.combine(d, t)

    def _to_minutes(self, t: time, is_end_time: bool = False) -> int:
        """時刻を分単位に変換
        
        Args:
            t: 変換する時刻
            is_end_time: 終了時刻として扱うかどうか
        
        Returns:
            int: 分単位の時刻（00:00は通常0分、終了時刻の場合は24:00=1440分として扱う）
        """
        minutes = t.hour * 60 + t.minute
        if minutes == 0 and is_end_time:  # 終了時刻の00:00のみ24:00として扱う
            return 24 * 60
        return minutes

    def find_available_slots(
        self,
        desired_range: TimeRange,
        duration_hours: int
    ) -> List[StudioAvailability]:
        """指定された条件に合う予約可能な時間枠を検索"""
        if duration_hours <= 0:
            raise StudioValidationError("利用時間は正の値である必要があります")
        
        result: List[StudioAvailability] = []
        min_duration_minutes = duration_hours * 60
        
        for availability in self.availabilities:
            filtered_slots = []
            
            # まず各スロットを調整してからフィルタリング
            for slot in availability.time_slots:
                start_minutes = self._to_minutes(slot.start_time, False)
                
                # 終了時刻を調整（30分スタートの場合は30分早める）
                end_minutes = self._to_minutes(slot.end_time, True)
                if availability.starts_at_thirty:
                    end_minutes -= 30
                
                # スロットの時間長が必要な時間以上であることを確認
                if end_minutes - start_minutes >= min_duration_minutes:
                    # 調整後の終了時刻でStudioTimeSlotを作成
                    if end_minutes == 24 * 60:
                        adjusted_end = time(0, 0)
                    else:
                        adjusted_end = time(
                            (end_minutes % 1440) // 60,
                            end_minutes % 60
                        )
                    
                    filtered_slots.append(StudioTimeSlot(
                        start_time=slot.start_time,
                        end_time=adjusted_end
                    ))
            
            # 連続したスロットをマージ
            merged_slots = self._merge_filtered_slots(filtered_slots, min_duration_minutes, availability)
            
            # 指定された時間範囲でフィルタリング
            valid_slots = self._filter_slots_in_range(
                merged_slots,
                desired_range,
                min_duration_minutes,
                availability
            )
            
            if valid_slots:
                result.append(StudioAvailability(
                    room_name=availability.room_name,
                    time_slots=valid_slots,
                    date=availability.date,
                    starts_at_thirty=availability.starts_at_thirty
                ))
        
        return result

    def _merge_filtered_slots(
        self,
        slots: List[StudioTimeSlot],
        min_duration_minutes: int,
        availability: StudioAvailability
    ) -> List[StudioTimeSlot]:
        """フィルタリング済みの時間枠をマージ"""
        if not slots:
            return []

        # 開始時刻でソート
        sorted_slots = sorted(slots, key=lambda x: self._to_minutes(x.start_time, False))
        merged = []
        current = sorted_slots[0]
        
        for next_slot in sorted_slots[1:]:
            current_end = self._to_minutes(current.end_time, True)
            next_start = self._to_minutes(next_slot.start_time, False)
            
            if current_end >= next_start:  # >=に変更して隣接するスロットもマージ
                # 連続しているのでマージ
                current = StudioTimeSlot(
                    start_time=current.start_time,
                    end_time=next_slot.end_time
                )
            else:
                # 現在の時間枠が最小時間以上であれば追加
                slot_duration = (
                    self._to_minutes(current.end_time, True) -
                    self._to_minutes(current.start_time, False)
                )
                if slot_duration >= min_duration_minutes:
                    merged.append(current)
                current = next_slot
        
        # 最後の時間枠を処理
        slot_duration = (
            self._to_minutes(current.end_time, True) -
            self._to_minutes(current.start_time, False)
        )
        if slot_duration >= min_duration_minutes:
            merged.append(current)
        
        return merged

    def _filter_slots_in_range(
        self,
        slots: List[StudioTimeSlot],
        desired_range: TimeRange,
        min_duration_minutes: int,
        availability: StudioAvailability
    ) -> List[StudioTimeSlot]:
        """指定された時間範囲内の時間枠をフィルタリング"""
        filtered = []
        range_start = self._to_minutes(desired_range.start, False)  # 開始時刻
        range_end = self._to_minutes(desired_range.end, True)  # 終了時刻
        
        for slot in slots:
            slot_start = self._to_minutes(slot.start_time, False)  # 開始時刻
            slot_end = self._to_minutes(slot.end_time, True)  # 終了時刻
            
            if slot_start < range_end and slot_end > range_start:
                new_start_minutes = max(slot_start, range_start)
                new_end_minutes = min(slot_end, range_end)
                
                # 時間枠の長さが最小時間以上であることを確認
                if new_end_minutes - new_start_minutes >= min_duration_minutes:
                    # minutes を time オブジェクトに変換
                    new_start = time(
                        (new_start_minutes % 1440) // 60,
                        new_start_minutes % 60
                    )
                    
                    # 終了時刻の処理
                    if new_end_minutes == 24 * 60:
                        new_end = time(0, 0)
                    else:
                        new_end = time(
                            (new_end_minutes % 1440) // 60,
                            new_end_minutes % 60
                        )
                    
                    # 30分スタートの部屋の場合は終了時刻を30分早める
                    if availability.starts_at_thirty:
                        if new_end_minutes == 24 * 60:
                            new_end = time(23, 30)
                        else:
                            end_minutes = new_end_minutes - 30
                            new_end = time(
                                (end_minutes % 1440) // 60,
                                end_minutes % 60
                            )
                    
                    filtered.append(StudioTimeSlot(
                        start_time=new_start,
                        end_time=new_end
                    ))
        
        return filtered

# メイン関数
if __name__ == "__main__":
    import logging
    from scraper_studiol import StudioOLScraper
    from scraper_padstudio import PadStudioScraper

    # ロギングの設定
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # テスト用の時間範囲（例：9:00-22:00）
    desired_range = TimeRange(time(9, 0), time(22, 0))
    # 異なる利用時間でテスト
    test_durations = [1, 2, 3]  # 1時間、2時間、3時間
    target_date = date(2025, 1, 7)

    def check_and_print_availability(availabilities, studio_name):
        if not availabilities:
            logger.warning(f"{studio_name}: 利用可能なスタジオが見つかりませんでした")
            return

        logger.info(f"{studio_name}: {len(availabilities)}件のスタジオ情報を取得しました")

        # AvailabilityCheckerの初期化
        checker = AvailabilityChecker(availabilities)

        for duration in test_durations:
            print(f"\n=== {studio_name}: {duration}時間枠での検索結果 ===")
            results = checker.find_available_slots(desired_range, duration)
            
            if not results:
                print(f"{duration}時間の利用可能枠は見つかりませんでした")
                continue
                
            for availability in results:
                print(f"\n部屋名: {availability.room_name}")
                print("予約可能時間枠:")
                for slot in availability.time_slots:
                    print(f"  {slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')}")
                if availability.starts_at_thirty:
                    print("  ※ この部屋は30分スタートの部屋です")

    try:
        # Studio-OLスクレイパーのテスト
        logger.info("Studio-OLスクレイパーを初期化中...")
        ol_scraper = StudioOLScraper()
        shop_id = "546"
        logger.info(f"shop_id: {shop_id} への接続を確立中...")
        ol_scraper.establish_connection(shop_id)
        logger.info(f"Studio-OL: 空き状況を取得中: {target_date}")
        ol_availabilities = ol_scraper.fetch_available_times(target_date)
        check_and_print_availability(ol_availabilities, "Studio-OL")

        # PAD Studioスクレイパーのテスト
        logger.info("\nPAD Studioスクレイパーを初期化中...")
        pad_scraper = PadStudioScraper()
        logger.info("PAD Studio: 接続を確立中...")
        pad_scraper.establish_connection()
        logger.info(f"PAD Studio: 空き状況を取得中: {target_date}")
        pad_availabilities = pad_scraper.fetch_available_times(target_date)
        check_and_print_availability(pad_availabilities, "PAD Studio")

    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}", exc_info=True)