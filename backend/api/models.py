from django.db import models

class Todo(models.Model):
    title = models.CharField(max_length=100)
    completed = models.BooleanField(default=False)
    attachment = models.FileField(upload_to='uploads/', blank=True, null=True)  # Optional file attachment

    def __str__(self):
        return self.titleS

class Studio(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    
    # 営業時間をTimeFieldで管理
    opening_time = models.TimeField(
        help_text="開店時間"
    )
    closing_time = models.TimeField(
        help_text="閉店時間"
    )
    # 閉店時間が翌日かどうかのフラグ
    closes_next_day = models.BooleanField(
        default=False,
        help_text="閉店時間が翌日の場合はTrue"
    )
    
    reservation_url = models.URLField()
    
    # 個人練習の予約開始タイミングを改善
    self_practice_reservation_start_date = models.DurationField(
        null=True,
        blank=True,
        help_text="個人練習の予約開始可能までの日にち"
    )
    
        # 個人練習の予約開始タイミングを改善
    self_practice_reservation_start_time = models.DurationField(
        null=True,
        blank=True,
        help_text="個人練習の予約開始可能時間"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
