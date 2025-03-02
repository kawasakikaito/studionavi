from datetime import datetime
from typing import Optional
from django.db.models import Q, Case, When, Value, FloatField
from django.db.models.functions import Greatest
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from api.scrapers.scraper_registry import AvailabilityService
from api.scrapers.reservation_checker import TimeRange, AvailabilityChecker
from .models import Studio, Todo
from .serializers import (
    StudioSerializer, 
    TodoSerializer, 
    AnalyzedStudioSerializer
)
from config.studio_config import STUDIO_CONFIGS, ScraperConfig


# 単純なヘルスチェックビュー
@api_view(['GET'])
def health_check(request):
    """
    簡単なヘルスチェックエンドポイント - いつも200応答
    ALBヘルスチェック用
    """
    from django.http import HttpResponse
    return HttpResponse('ok', content_type='text/plain', status=200)


class TodoViewSet(viewsets.ModelViewSet):
    queryset = Todo.objects.all()
    serializer_class = TodoSerializer


class StudioViewSet(viewsets.ModelViewSet):
    """スタジオ情報を管理するViewSet"""
    
    queryset = Studio.objects.all()
    serializer_class = StudioSerializer
    result_limit = 10
    availability_service = AvailabilityService()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.availability_service.initialize_scrapers()

    def _get_scraper_config(self, studio_id: str) -> Optional[ScraperConfig]:
        """スタジオIDに対応するスクレイパー設定を取得"""
        config = STUDIO_CONFIGS.get(studio_id)
        return config.scraper if config else None

    @action(detail=False, methods=['get'])
    def search(self, request):
        """スタジオを検索するエンドポイント
        
        DBから検索を行い, 利用可能なスクレイパーの情報を付加して返す
        
        Query Parameters:
            q (str): 検索クエリ
        """
        query = request.query_params.get('q', '')
        if not query:
            return Response([])
            
        # DBからの検索
        queryset = self.get_queryset().annotate(
            relevance=Greatest(
                # 完全一致は最高スコア
                Case(
                    When(name__iexact=query, then=Value(100)),
                    When(address__iexact=query, then=Value(100)),
                    default=Value(0),
                    output_field=FloatField(),
                ),
                # 前方一致は次に高いスコア
                Case(
                    When(name__istartswith=query, then=Value(80)),
                    When(address__istartswith=query, then=Value(80)),
                    default=Value(0),
                    output_field=FloatField(),
                ),
                # 部分一致は最低スコア
                Case(
                    When(name__icontains=query, then=Value(60)),
                    When(address__icontains=query, then=Value(60)),
                    default=Value(0),
                    output_field=FloatField(),
                ),
            )
        ).filter(
            Q(name__icontains=query) |
            Q(address__icontains=query)
        ).order_by('-relevance')[:self.result_limit]

        # スクレイピング設定の追加
        serializer = self.get_serializer(queryset, many=True)
        results = serializer.data
        
        # ConfigからスクレイピングIDを付与
        for result in results:
            studio_id = str(result['id'])
            scraper_config = self._get_scraper_config(studio_id)
            if scraper_config:
                result['scraper_type'] = scraper_config.scraper_type
                result['shop_id'] = scraper_config.shop_id
                result['has_availability'] = True
            else:
                result['scraper_type'] = None
                result['shop_id'] = None
                result['has_availability'] = False

        return Response(results)

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """スタジオの空き状況を取得するエンドポイント
        
        Path Parameters:
            pk (str): スタジオID

        Query Parameters:
            date (str): 対象日付 (YYYY-MM-DD)
            start (str): 開始時刻 (HH:MM)
            end (str): 終了時刻 (HH:MM)
            duration (str): 利用時間（時間単位）
        """
        # まずDBからスタジオの基本情報を取得
        studio = self.get_object()
        
        # Configからスクレイパー設定を取得
        scraper_config = self._get_scraper_config(str(studio.id))
        if not scraper_config:
            return Response({
                'status': 'error',
                'error': {
                    'code': 'STUDIO_NOT_CONFIGURED',
                    'message': 'このスタジオは空き状況確認に対応していません'
                }
            }, status=status.HTTP_404_NOT_FOUND)

        # パラメータのバリデーション
        try:
            date_str = request.query_params.get('date')
            start_time = request.query_params.get('start')
            end_time = request.query_params.get('end')
            duration = request.query_params.get('duration')

            if not all([date_str, start_time, end_time, duration]):
                raise ValidationError('必須パラメータが不足しています')

            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            duration_hours = int(duration)

            # 24:00の特別処理
            if end_time == "24:00":
                end_time = "23:59"  # 一時的に23:59として処理

            start_time = datetime.strptime(start_time, '%H:%M').time()
            end_time = datetime.strptime(end_time, '%H:%M').time()

        except ValueError as e:
            raise ValidationError(f'パラメータが不正です: {str(e)}')

        try:
            # スタジオの空き状況を取得
            availabilities = self.availability_service.get_availability(
                studio_id=scraper_config.scraper_type,
                shop_id=scraper_config.shop_id,
                target_date=target_date
            )

            # 空き状況チェッカーを初期化
            checker = AvailabilityChecker(availabilities)
            time_range = TimeRange(start=start_time, end=end_time)
            
            # 利用可能な時間枠を検索
            available_slots = checker.find_available_slots(time_range, duration_hours)
            
            # レスポンスの生成
            response_data = {
                'status': 'success',
                'data': {
                    'studio_id': str(studio.id),
                    'studio_name': studio.name,
                    'date': target_date.isoformat(),
                    'available_ranges': [
                        {
                            'start': time_slot.start_time.strftime('%H:%M'),
                            'end': '24:00' if time_slot.end_time.strftime('%H:%M') == '23:59' else time_slot.end_time.strftime('%H:%M'),
                            'room_name': availability.room_name,
                            'start_minutes': availability.start_minutes
                        }
                        for availability in available_slots
                        for time_slot in availability.time_slots
                    ],
                    'meta': {
                        'timezone': 'Asia/Tokyo'
                    }
                }
            }

            # シリアライザでバリデーションと整形
            serializer = AnalyzedStudioSerializer(data=response_data)
            serializer.is_valid(raise_exception=True)

            return Response(serializer.validated_data)

        except Exception as e:
            return Response({
                'status': 'error',
                'error': {
                    'code': 'AVAILABILITY_FETCH_ERROR',
                    'message': str(e)
                }
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)