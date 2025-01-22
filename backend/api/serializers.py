from rest_framework import serializers
from .models import *

class TodoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Todo
        fields = ['id', 'title', 'completed', 'attachment']

class StudioSerializer(serializers.ModelSerializer):
    hours = serializers.SerializerMethodField()
    self_booking_start = serializers.SerializerMethodField()
    
    class Meta:
        model = Studio
        fields = ['id', 'name', 'address', 'hours', 'self_booking_start']
    
    def get_hours(self, obj):
        opening = obj.opening_time.strftime("%H:%M")
        closing = obj.closing_time.strftime("%H:%M")
        next_day = "翌" if obj.closes_next_day else ""
        return f"{opening} - {next_day}{closing}"
    
    def get_self_booking_start(self, obj):
        if obj.self_practice_reservation_start_date and obj.self_practice_reservation_start_time:
            if obj.self_practice_reservation_start_date == 1:
                date_part = "前日"
            else:
                date_part = f"{obj.self_practice_reservation_start_date}日前"
            
            time = obj.self_practice_reservation_start_time
            time_part = time.strftime("%H:%M")
            
            return f"{date_part} {time_part}〜"

class AvailableTimeRangeSerializer(serializers.Serializer):
    start = serializers.CharField()
    end = serializers.CharField()
    room_name = serializers.CharField()
    start_minutes = serializers.ListField(
        child=serializers.IntegerField(
            min_value=0,
            max_value=59
        ),
        help_text="予約開始可能な時刻（分）のリスト。例: [0, 30]"
    )

class StudioAvailabilityDataSerializer(serializers.Serializer):
    studio_id = serializers.CharField()
    studio_name = serializers.CharField()
    date = serializers.CharField()
    available_ranges = AvailableTimeRangeSerializer(many=True)
    meta = serializers.DictField()

class AnalyzedStudioSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = StudioAvailabilityDataSerializer()