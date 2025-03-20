from .base import *

# デバッグモードを無効化
DEBUG = False

# 本番環境用の設定
ALLOWED_HOSTS = ['*']  # 後で適切なドメインに制限する

# CORS設定
CORS_ALLOW_ALL_ORIGINS = False  # 全てのオリジンを許可しない
CORS_ALLOWED_ORIGINS = [
    "http://studionavi-alb-837030228.ap-northeast-1.elb.amazonaws.com",
    "https://studionavi-alb-837030228.ap-northeast-1.elb.amazonaws.com",
    # 必要に応じて他のオリジンを追加
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# corsheadersはすでにbase.pyのTHIRD_PARTY_APPSに含まれているため、ここでは追加しない
# ミドルウェアの設定
# DisableSSLRedirectMiddlewareをSecurityMiddlewareの前に配置
MIDDLEWARE = [
    'api.middleware.DisableSSLRedirectMiddleware',  # HTTPSリダイレクトを無効化
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'api.middleware.HealthCheckMiddleware',  # ヘルスチェック用ミドルウェア
]

# 静的ファイルの設定
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# セキュリティ設定
# HTTPSリダイレクトを無効化
SECURE_SSL_REDIRECT = False
SECURE_REDIRECT_EXEMPT = ['*']  # すべてのパスを除外
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# SSL/HTTPS settings
# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # HTTPSが設定されていないためコメントアウト

# リダイレクトから除外するパス（ヘルスチェック用）
SECURE_REDIRECT_EXEMPT = [
    r"^health/?$",
    r"^api/health/?$",
    r"^health$",
    r"^api/health$",
    r"^api/?$",  # APIルートも除外
    r"^api/.*$",  # APIパスすべてを除外
]

# URLの末尾スラッシュリダイレクトを無効化（ヘルスチェック用）
APPEND_SLASH = False

# HTTPSリダイレクトを無効化するための追加設定
SECURE_REDIRECT_EXEMPT = ['.*']  # すべてのパスを除外

# データベース設定
import dj_database_url

# ロギングの設定（デバッグ用）
print("production.py設定を読み込んでいます")
print(f"DATABASE_URL環境変数: {'存在します' if 'DATABASE_URL' in os.environ else '存在しません'}")
if 'DATABASE_URL' in os.environ:
    print(f"DATABASE_URL値: {os.environ.get('DATABASE_URL')[:10]}...")  # セキュリティのため全部は表示しない

# DATABASE_URL環境変数が設定されている場合はそれを使用
if 'DATABASE_URL' in os.environ:
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
    print("dj_database_urlを使用してデータベース設定を行いました")
else:
    # 従来の設定（ローカル開発用）
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
    print("従来のデータベース設定を使用しています - HOST: {}".format(os.environ.get('DB_HOST', 'db')))

# ロギング設定を強化
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# データベース接続情報をログに出力
import logging
logger = logging.getLogger('django')
logger.info('Django設定: production.py')
if 'DATABASE_URL' in os.environ:
    logger.info('データベース設定: DATABASE_URL使用')
else:
    logger.info(f'データベース設定: 従来設定 (HOST={os.environ.get("DB_HOST", "db")})')
