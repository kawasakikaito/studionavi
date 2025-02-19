import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logger(name: str, log_dir: Path = Path("logs")) -> logging.Logger:
    """アプリケーション全体で使用するロガーのセットアップ
    
    Args:
        name: ロガーの名前（通常は__name__）
        log_dir: ログファイルを保存するディレクトリ
        
    Returns:
        設定済みのロガーインスタンス
    """
    # ロガーの取得
    logger = logging.getLogger(name)
    
    # 既に設定済みの場合は既存のロガーを返す
    if logger.handlers:
        return logger
        
    # ログレベルの設定
    logger.setLevel(logging.DEBUG)
    
    # ログディレクトリの作成
    log_dir.mkdir(exist_ok=True)
    
    # ログファイルのパス
    log_file = log_dir / f"{name.split('.')[-1]}.log"
    
    # ローテーションファイルハンドラーの設定
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    # フォーマッターの設定
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    # ハンドラーの追加
    logger.addHandler(file_handler)
    
    # 初期化ログ
    logger.info(f"ロガーを初期化: name={name}, log_file={log_file}")
    
    return logger
