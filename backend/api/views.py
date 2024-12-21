from rest_framework import viewsets
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import *
from .serializers import *

class TodoViewSet(viewsets.ModelViewSet):
    queryset = Todo.objects.all()
    serializer_class = TodoSerializer

class StudioViewSet(viewsets.ModelViewSet):
    queryset = Studio.objects.all()
    serializer_class = StudioSerializer

    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        if not query:
            return Response([])
            
        queryset = self.get_queryset().filter(
            Q(name__icontains=query) |
            Q(address__icontains=query)
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)