import logging
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
    
    # ファイルハンドラーの設定
    file_handler = logging.FileHandler(
        log_dir / f"{name.split('.')[-1]}.log",
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
    
    return logger