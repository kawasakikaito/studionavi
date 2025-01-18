from django.db import models
from django.core.exceptions import ValidationError
from datetime import time

class Todo(models.Model):
    title = models.CharField(max_length=100)
    completed = models.BooleanField(default=False)
    attachment = models.FileField(upload_to='uploads/', blank=True, null=True)  # Optional file attachment

    def __str__(self):
        return self.title

class Studio(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
        
    # 24時間営業フラグを追加
    is_24h = models.BooleanField(
        default=False,
        help_text="24時間営業の場合はTrue"
    )
    
    # 既存のフィールドはnull=True, blank=Trueに変更
    opening_time = models.TimeField(
        null=True,
        blank=True,
        help_text="開店時間（24時間営業の場合は空）"
    )
    closing_time = models.TimeField(
        null=True,
        blank=True,
        help_text="閉店時間（24時間営業の場合は空）"
    )
    # 閉店時間が翌日かどうかのフラグ
    closes_next_day = models.BooleanField(
        default=False,
        help_text="閉店時間が翌日の場合はTrue"
    )
    
    reservation_url = models.URLField()
    
    self_practice_reservation_start_date = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="個人練習の予約開始可能までの日数（例：7日前）"
    )
    self_practice_reservation_start_time = models.TimeField(
        null=True,
        blank=True,
        help_text="個人練習の予約開始時間"
    )

    # 作成日時と更新日時
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """データの整合性をチェック"""
        if self.is_24h:
            # 24時間営業の場合は営業時間を空にする
            if self.opening_time or self.closing_time:
                raise ValidationError(
                    "24時間営業の場合、開店時間と閉店時間は空にしてください。"
                )
        else:
            # 通常営業の場合は営業時間が必須
            if not self.opening_time or not self.closing_time:
                raise ValidationError(
                    "通常営業の場合、開店時間と閉店時間は必須です。"
                )

    def is_open_at(self, check_time: time) -> bool:
        """指定された時刻に営業しているかをチェック"""
        if self.is_24h:
            return True
            
        if not self.opening_time or not self.closing_time:
            return False
            
        if self.closes_next_day:
            # 翌日まで営業している場合
            if self.opening_time <= check_time:
                return True
            if check_time <= self.closing_time:
                return True
            return False
        else:
            # 当日中に閉店する場合
            return self.opening_time <= check_time <= self.closing_time

    def __str__(self):
        return self.name

class User(models.Model):
    user_id = models.IntegerField(unique=True)  # ユーザーID（ユニーク）
    name = models.CharField(max_length=100)  # ユーザー名
    password = models.CharField(max_length=255)  # パスワード（ハッシュ化推奨）
    created_at = models.DateTimeField(auto_now_add=True)  # 作成日時
    updated_at = models.DateTimeField(auto_now=True)  # 更新日時

    def __str__(self):
        return self.name

# お気に入りスタジオ
class FavoriteStudio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorite_studios")
    studio = models.ForeignKey(Studio, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)  # 登録日時

    class Meta:
        unique_together = ('user', 'studio')  # 同じスタジオを重複登録不可

    def save(self, *args, **kwargs):
        # ユーザーがすでに5つ登録している場合はエラーをスロー
        if FavoriteStudio.objects.filter(user=self.user).count() >= 5:
            raise ValueError("お気に入りスタジオは最大5つまでです。")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.name} - {self.studio.name}"
