import os
import logging
from pathlib import Path

# 環境変数からDJANGO_ENVIRONMENTを取得（デフォルトは'development'）
ENVIRONMENT = os.environ.get('DJANGO_ENVIRONMENT', 'development')

# .envファイルのパスを設定
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / f'.env.{ENVIRONMENT}'
DEFAULT_ENV_FILE = BASE_DIR / '.env'

# python-dotenvをインポート
try:
    from dotenv import load_dotenv
    # 環境固有の.envファイルが存在すれば読み込む、なければデフォルトの.envを読み込む
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE)
        print(f"=== {ENVIRONMENT}環境用の.envファイル({ENV_FILE})を読み込みました ===")
    elif DEFAULT_ENV_FILE.exists():
        load_dotenv(DEFAULT_ENV_FILE)
        print(f"=== デフォルトの.envファイルを読み込みました ===")
    else:
        print("=== .envファイルが見つかりませんでした。環境変数を使用します ===")
except ImportError:
    print("python-dotenvがインストールされていません。環境変数のみを使用します。")

# 環境に応じた設定ファイルをインポート
if ENVIRONMENT == 'production':
    print("=== 本番環境設定を読み込みます ===")
    from .production import *
else:
    print("=== 開発環境設定が読み込まれました ===")
    from .development import *

# デバッグ情報を出力
print(f"DEBUG設定値: {DEBUG}")
print(f"ALLOWED_HOSTS設定値: {ALLOWED_HOSTS}")
