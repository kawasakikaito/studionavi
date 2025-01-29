import unittest
from datetime import time, date
from api.scrapers.reservation_checker import (
    StudioTimeSlot,
    StudioAvailability,
    TimeRange,
    AvailabilityChecker,
    StudioValidationError
)

class TestReservationChecker(unittest.TestCase):
    def setUp(self):
        # テスト用の時間枠を作成
        self.time_slot1 = StudioTimeSlot(
            start_time=time(9, 0),
            end_time=time(12, 0)
        )
        self.time_slot2 = StudioTimeSlot(
            start_time=time(13, 0),
            end_time=time(18, 0)
        )
        self.time_slot3 = StudioTimeSlot(
            start_time=time(22, 0),
            end_time=time(0, 0)  # 24:00として扱われる
        )

    def test_normal_reservation(self):
        """通常の予約（0分スタート）のテスト"""
        # スタジオの設定
        availability = StudioAvailability(
            room_name="Studio A",
            date=date(2025, 1, 28),
            time_slots=[self.time_slot1],  # 9:00-12:00
            start_minutes=[0],  # 0分スタートのみ
            allows_thirty_minute_slots=False
        )
        
        checker = AvailabilityChecker([availability])
        
        # 10:00-11:00で1時間の予約を試みる
        result = checker.find_available_slots(
            TimeRange(time(10, 0), time(11, 0)),
            duration_hours=1.0
        )
        
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0].time_slots), 1)
        slot = result[0].time_slots[0]
        self.assertEqual(slot.start_time, time(10, 0))
        self.assertEqual(slot.end_time, time(11, 0))

    def test_thirty_minute_start(self):
        """30分スタートの予約テスト"""
        # スタジオの設定
        availability = StudioAvailability(
            room_name="Studio B",
            date=date(2025, 1, 28),
            time_slots=[self.time_slot1],  # 9:00-12:00
            start_minutes=[30],  # 30分スタートのみ
            allows_thirty_minute_slots=True
        )
        
        checker = AvailabilityChecker([availability])
        
        # 10:00-11:00で予約を試みる（失敗するはず）
        result1 = checker.find_available_slots(
            TimeRange(time(10, 0), time(11, 0)),
            duration_hours=1.0
        )
        self.assertEqual(len(result1), 0)  # 0分スタートは不可能なので結果は空
        
        # 10:30-11:30で予約を試みる（成功するはず）
        result2 = checker.find_available_slots(
            TimeRange(time(10, 30), time(11, 30)),
            duration_hours=1.0
        )
        self.assertEqual(len(result2), 1)
        self.assertEqual(len(result2[0].time_slots), 1)
        slot = result2[0].time_slots[0]
        self.assertEqual(slot.start_time, time(10, 30))
        self.assertEqual(slot.end_time, time(11, 30))

    def test_multiple_start_minutes(self):
        """複数の開始時刻を持つスタジオのテスト"""
        # スタジオの設定
        availability = StudioAvailability(
            room_name="Studio C",
            date=date(2025, 1, 28),
            time_slots=[self.time_slot1],  # 9:00-12:00
            start_minutes=[0, 30],  # 0分と30分スタート
            allows_thirty_minute_slots=True
        )
        
        checker = AvailabilityChecker([availability])
        
        # 10:00-11:00で予約を試みる
        result1 = checker.find_available_slots(
            TimeRange(time(10, 0), time(11, 0)),
            duration_hours=1.0
        )
        self.assertEqual(len(result1), 1)
        self.assertEqual(len(result1[0].time_slots), 1)
        
        # 10:30-11:30で予約を試みる
        result2 = checker.find_available_slots(
            TimeRange(time(10, 30), time(11, 30)),
            duration_hours=1.0
        )
        self.assertEqual(len(result2), 1)
        self.assertEqual(len(result2[0].time_slots), 1)

    def test_overnight_reservation(self):
        """日付をまたぐ予約のテスト"""
        # スタジオの設定
        availability = StudioAvailability(
            room_name="Studio D",
            date=date(2025, 1, 28),
            time_slots=[self.time_slot3],  # 22:00-24:00
            start_minutes=[0],
            allows_thirty_minute_slots=False
        )
        
        checker = AvailabilityChecker([availability])
        
        # 23:00-24:00で予約を試みる
        result = checker.find_available_slots(
            TimeRange(time(23, 0), time(0, 0)),
            duration_hours=1.0
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0].time_slots), 1)
        slot = result[0].time_slots[0]
        self.assertEqual(slot.start_time, time(23, 0))
        self.assertEqual(slot.end_time, time(0, 0))

    def test_edge_cases(self):
        """エッジケースのテスト"""
        # スタジオの設定
        availability = StudioAvailability(
            room_name="Studio E",
            date=date(2025, 1, 28),
            time_slots=[self.time_slot2],  # 13:00-18:00
            start_minutes=[0, 30],
            allows_thirty_minute_slots=True
        )
        
        checker = AvailabilityChecker([availability])
        
        # 短い予約時間（0.5時間）
        result1 = checker.find_available_slots(
            TimeRange(time(14, 0), time(14, 30)),
            duration_hours=0.5
        )
        self.assertEqual(len(result1), 1)
        
        # 長い予約時間（5時間）
        result2 = checker.find_available_slots(
            TimeRange(time(13, 0), time(18, 0)),
            duration_hours=5.0
        )
        self.assertEqual(len(result2), 1)
        
        # 無効な予約時間（0時間）
        with self.assertRaises(StudioValidationError):
            checker.find_available_slots(
                TimeRange(time(14, 0), time(15, 0)),
                duration_hours=0
            )
        
        # 範囲外の予約
        result3 = checker.find_available_slots(
            TimeRange(time(17, 30), time(19, 0)),
            duration_hours=1.0
        )
        self.assertEqual(len(result3), 0)

if __name__ == '__main__':
    unittest.main()
