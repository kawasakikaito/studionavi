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

# セキュリティ設定
SECURE_SSL_REDIRECT = False  # HTTPSリダイレクトを無効化（一時的な対応）
SESSION_COOKIE_SECURE = False  # HTTPでもCookieを使用可能に（一時的な対応）
CSRF_COOKIE_SECURE = False  # HTTPでもCSRFトークンを使用可能に（一時的な対応）
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
}
