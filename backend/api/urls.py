from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register('todos', TodoViewSet, basename='todo')
router.register("studios", StudioViewSet, basename="studio")

urlpatterns = [
    path('', include(router.urls)),
]