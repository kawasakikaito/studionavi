import logging

logger = logging.getLogger('django')

class HealthCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 明確なヘルスチェックパスをリストで定義（ALBヘルスチェック用）
        health_check_paths = ['/', '/health', '/health/']
        
        # パスが完全一致でヘルスチェックパスなら直接応答
        if request.path in health_check_paths:
            from django.http import HttpResponse
            return HttpResponse('ok', content_type='text/plain', status=200)
        
        # 通常の処理を続行
        response = self.get_response(request)
        return response
