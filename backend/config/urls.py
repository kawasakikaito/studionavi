"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

# ルートパスのヘルスチェック
def simple_health_check(request):
    """
    最もシンプルなヘルスチェックエンドポイント
    ALBヘルスチェック用
    """
    return HttpResponse('ok', content_type='text/plain', status=200)

urlpatterns = [
    # ヘルスチェックエンドポイント
    path('', simple_health_check, name='root'),
    path('health', simple_health_check, name='health_no_slash'),
    path('health/', simple_health_check, name='health'),
    
    # 通常のAPIルート
    path('api/', include('api.urls')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)