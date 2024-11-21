from rest_framework import serializers
from .models import *

class TodoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Todo
        fields = ['id', 'title', 'completed', 'attachment']  # Include necessary fields

class StudioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Studio
        fields = ['name', 'address']  # Include necessary fields