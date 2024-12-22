import factory
from datetime import time, timedelta
from django.utils import timezone
from api.models import Studio

class StudioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Studio

    name = factory.Sequence(lambda n: f'スタジオ{n+1}')
    address = factory.Sequence(lambda n: f'東京都渋谷区代々木{n+1}-{n+1}-{n+1}')
    
    # 営業時間は10:00-22:00をデフォルトとする
    opening_time = factory.LazyFunction(lambda: time(10, 0))
    closing_time = factory.LazyFunction(lambda: time(22, 0))
    closes_next_day = False
    
    reservation_url = factory.Sequence(lambda n: f'https://example.com/studio/{n+1}')
    
    # 予約開始タイミング: デフォルトで7日前から予約可能
    self_practice_reservation_start_date = factory.LazyFunction(lambda: 1)
    # 予約開始時間: デフォルトで0時0分
    self_practice_reservation_start_time = factory.LazyFunction(lambda: time(7, 0))
    
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)