"""
カスタムミドルウェアモジュール
HTTPSリダイレクトを無効化し、本番環境でのAPI通信を改善するためのミドルウェアを提供します
"""
import logging

logger = logging.getLogger(__name__)

class DisableHttpsRedirectMiddleware:
    """
    HTTPSリダイレクトを無効化するミドルウェア
    
    Djangoの標準SecurityMiddlewareによるHTTPSリダイレクトを上書きして、
    HTTPでのアクセスを許可します。
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        logger.info("DisableHttpsRedirectMiddleware が初期化されました")
        
    def __call__(self, request):
        # リクエスト処理前の操作
        original_scheme = request.META.get('wsgi.url_scheme', 'http')
        logger.debug(f"リクエスト処理前: scheme={original_scheme}, path={request.path}")
        
        # HTTPSリダイレクトを防ぐためのヘッダーを設定
        request.META['wsgi.url_scheme'] = 'http'
        request.META['HTTP_X_FORWARDED_PROTO'] = 'http'
        
        # SecurityMiddlewareの_should_redirectメソッドをモンキーパッチ
        from django.middleware.security import SecurityMiddleware
        original_should_redirect = getattr(SecurityMiddleware, '_should_redirect', None)
        if original_should_redirect:
            SecurityMiddleware._should_redirect = lambda self, request: False
            logger.debug("SecurityMiddlewareの_should_redirectメソッドをモンキーパッチしました")
        
        # 次のミドルウェアまたはビューを呼び出す
        response = self.get_response(request)
        
        # レスポンス処理後の操作
        logger.debug(f"レスポンス処理後: status={response.status_code}, headers={dict(response.items())}")
        
        # HTTPSリダイレクトのLocationヘッダーを削除または修正
        if response.status_code in (301, 302, 307, 308) and 'Location' in response:
            location = response['Location']
            if location.startswith('https://'):
                # HTTPSをHTTPに置き換える
                http_location = 'http://' + location[8:]
                response['Location'] = http_location
                logger.info(f"HTTPSリダイレクトを修正: {location} -> {http_location}")
            
            # リダイレクトを完全に無効化する場合は以下のコードを使用
            # del response['Location']
            # response.status_code = 200
            # logger.info(f"リダイレクトを無効化: 元のステータス={response.status_code}, URL={location}")
        
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        ビュー処理前のフック
        """
        logger.debug(f"process_view: view={view_func.__name__ if hasattr(view_func, '__name__') else str(view_func)}")
        return None
