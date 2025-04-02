from .base import *

# デバッグモードを無効化
DEBUG = False

# 本番環境用の設定
ALLOWED_HOSTS = ['*']  # 後で適切なドメインに制限する

# 静的ファイルの設定
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# CORS設定
CORS_ALLOWED_ORIGINS = [
    'http://studionavi-alb-837030228.ap-northeast-1.elb.amazonaws.com',
]

CSRF_TRUSTED_ORIGINS = [
    'http://studionavi-alb-837030228.ap-northeast-1.elb.amazonaws.com',
]

# すべてのオリジンからのリクエストを許可（一時的な対応）
CORS_ALLOW_ALL_ORIGINS = True

# カスタムミドルウェアを追加
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'api.middleware.DisableHttpsRedirectMiddleware',  # HTTPSリダイレクト無効化ミドルウェアを追加
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# セキュリティ設定 - HTTPSリダイレクトを確実に無効化
SECURE_PROXY_SSL_HEADER = None
SECURE_SSL_REDIRECT = False  # HTTPSリダイレクトを無効化（一時的な対応）
SESSION_COOKIE_SECURE = False  # HTTPでもCookieを使用可能に（一時的な対応）
CSRF_COOKIE_SECURE = False  # HTTPでもCSRFトークンを使用可能に（一時的な対応）
SECURE_HSTS_SECONDS = 0  # HSTSを無効化（一時的な対応）
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# データベース設定
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'studionavi'),
        'USER': os.environ.get('DB_USER', 'studionavi'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'studionavi_password'),
        'HOST': os.environ.get('DB_HOST', 'db'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# ロギング設定
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG',  # リクエスト処理の詳細なログを出力
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console'],
            'level': 'DEBUG',  # セキュリティ関連の詳細なログを出力
            'propagate': False,
        },
    },
}
