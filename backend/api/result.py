class SearchResult:
    def __init__(self, studio_name, studio_url, self_practice_reservation_start_time, is_available):
        self.studio_name = studio_name  # スタジオ名
        self.studio_url = studio_url  # スタジオURL
        self.self_practice_reservation_start_time = self_practice_reservation_start_time  # 個人練習予約開始時間
        self.is_available = is_available  # 予約可能か