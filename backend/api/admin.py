from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Studio, User, FavoriteStudio

admin.site.register(Studio)
admin.site.register(User)
admin.site.register(FavoriteStudio)