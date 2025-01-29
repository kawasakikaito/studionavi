from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from . import auth

router = DefaultRouter()
router.register("studios", StudioViewSet, basename="studio")

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', auth.register, name='register'),
]