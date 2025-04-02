"""
カスタムミドルウェアモジュール
HTTPSリダイレクトを無効化し、本番環境でのAPI通信を改善するためのミドルウェアを提供します
"""

class DisableHttpsRedirectMiddleware:
    """
    HTTPSリダイレクトを無効化するミドルウェア
    
    Djangoの標準SecurityMiddlewareによるHTTPSリダイレクトを上書きして、
    HTTPでのアクセスを許可します。
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # リクエスト処理前の操作
        # HTTPSリダイレクトを防ぐためのヘッダーを設定
        request.META['wsgi.url_scheme'] = 'http'
        
        # 次のミドルウェアまたはビューを呼び出す
        response = self.get_response(request)
        
        # レスポンス処理後の操作
        # HTTPSリダイレクトのLocationヘッダーを削除
        if response.status_code == 301 and 'Location' in response:
            location = response['Location']
            if location.startswith('https://'):
                # HTTPSをHTTPに置き換える
                http_location = 'http://' + location[8:]
                response['Location'] = http_location
                print(f"HTTPSリダイレクトを修正: {location} -> {http_location}")
        
        return response
