from django.db import models

class Todo(models.Model):
    title = models.CharField(max_length=100)
    completed = models.BooleanField(default=False)
    attachment = models.FileField(upload_to='uploads/', blank=True, null=True)  # Optional file attachment

    def __str__(self):
        return self.title

class Studio(models.Model):
    name = models.CharField(max_length=100)  # スタジオ名
    address = models.TextField()  # 住所
    opening_time = models.TimeField()  # 開店時間
    closing_time = models.TimeField()  # 閉店時間
    reservation_url = models.URLField()  # 予約ページのURL
    self_practice_reservation_start_time = models.IntegerField( # 個人練習の予約開始時間
        null=True,  # データベースでNULLを許可
        blank=True  # フォームや管理画面で空欄を許可
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 作成日時
    updated_at = models.DateTimeField(auto_now=True)  # 更新日時

    def __str__(self):
        return self.name

class User(models.Model):
    user_id = models.IntegerField(unique=True)  # ユーザーID（ユニーク）
    name = models.CharField(max_length=100)  # ユーザー名
    password = models.CharField(max_length=255)  # パスワード（ハッシュ化推奨）
    favorite_studio_1 = models.ForeignKey(
        Studio,  # お気に入りのスタジオ
        on_delete=models.SET_NULL,  # スタジオが削除された場合はNULLにする
        null=True,  # データベースでNULLを許可
        blank=True  # フォームや管理画面で空欄を許可
    )
    favorite_studio_2 = models.ForeignKey(
        Studio,  # お気に入りのスタジオ
        on_delete=models.SET_NULL,  # スタジオが削除された場合はNULLにする
        null=True,  # データベースでNULLを許可
        blank=True  # フォームや管理画面で空欄を許可
    )
    favorite_studio_3 = models.ForeignKey(
        Studio,  # お気に入りのスタジオ
        on_delete=models.SET_NULL,  # スタジオが削除された場合はNULLにする
        null=True,  # データベースでNULLを許可
        blank=True  # フォームや管理画面で空欄を許可
    )
    favorite_studio_4 = models.ForeignKey(
        Studio,  # お気に入りのスタジオ
        on_delete=models.SET_NULL,  # スタジオが削除された場合はNULLにする
        null=True,  # データベースでNULLを許可
        blank=True  # フォームや管理画面で空欄を許可
    )
    favorite_studio_5 = models.ForeignKey(
        Studio,  # お気に入りのスタジオ
        on_delete=models.SET_NULL,  # スタジオが削除された場合はNULLにする
        null=True,  # データベースでNULLを許可
        blank=True  # フォームや管理画面で空欄を許可
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 作成日時
    updated_at = models.DateTimeField(auto_now=True)  # 更新日時

    def __str__(self):
        return self.name

# 予約リクエストモデル
class SearchRequest(models.Model):
    studios = models.ManyToManyField(Studio)  # 選択したスタジオ
    search_start_datetime = models.DateTimeField()  # 検索起点時間
    search_end_datetime = models.DateTimeField()  # 検索終点時間
    reservation_time = models.DateTimeField()  # 希望予約時間
    
    def __str__(self):
        return (
            f"ユーザーID: {self.user_id}, "
            f"検索期間: {self.search_start_datetime} 〜 {self.search_end_datetime}, "
            f"希望予約時間: {self.reservation_time}"
        )
        
# 空き状況モデル
class AvailabilityResult(models.Model):
    reservation_request = models.ForeignKey(SearchRequest, on_delete=models.CASCADE)  # リクエスト情報
    studio = models.ForeignKey(Studio, on_delete=models.CASCADE)  # 対象スタジオ
    is_available = models.BooleanField()  # 空き状況
    message = models.TextField(blank=True, null=True)  # 追加情報
    checked_at = models.DateTimeField(auto_now_add=True)  # チェック日時

    def __str__(self):
        return f"{self.studio.name} - {'Available' if self.is_available else 'Not Available'}"