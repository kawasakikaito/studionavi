from rest_framework import serializers
from .models import *

class TodoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Todo
        fields = ['id', 'title', 'completed', 'attachment']  # Include necessary fields

class StudioSerializer(serializers.ModelSerializer):
    hours = serializers.SerializerMethodField()
    self_booking_start = serializers.SerializerMethodField()

    class Meta:
        model = Studio
        fields = ['id', 'name', 'address', 'hours', 'self_booking_start']

    def get_hours(self, obj):
        # 営業時間を "HH:MM - HH:MM" 形式で返す
        opening = obj.opening_time.strftime("%H:%M")
        closing = obj.closing_time.strftime("%H:%M")
        next_day = "翌" if obj.closes_next_day else ""
        return f"{opening} - {next_day}{closing}"

    def get_self_booking_start(self, obj):
        # 予約開始時期の文字列を生成
        if obj.self_practice_reservation_start_date and obj.self_practice_reservation_start_time:
            date_part = f"{obj.self_practice_reservation_start_date.days}日"
            time_part = f"{obj.self_practice_reservation_start_time.seconds // 3600}時間"
            return f"{date_part}{time_part}前から予約可能"
        return "予約開始時期未設定"