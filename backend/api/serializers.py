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
        if obj.self_practice_reservation_start_date and obj.self_practice_reservation_start_time:
            # 日付部分の処理
            if obj.self_practice_reservation_start_date == 1:
                date_part = "前日"
            else:
                date_part = f"{obj.self_practice_reservation_start_date}日前"
            
            # 時間部分の処理
            time = obj.self_practice_reservation_start_time
            time_part = time.strftime("%H:%M")
        
        return f"{date_part} {time_part}〜"