from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Case, When, Value, FloatField
from django.db.models.functions import Greatest
from .models import *
from .serializers import *

class TodoViewSet(viewsets.ModelViewSet):
    queryset = Todo.objects.all()
    serializer_class = TodoSerializer

class StudioViewSet(viewsets.ModelViewSet):
    queryset = Studio.objects.all()
    serializer_class = StudioSerializer
    result_limit = 10

    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        if not query:
            return Response([])
            
        # 検索クエリとの関連度をスコア化
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

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)