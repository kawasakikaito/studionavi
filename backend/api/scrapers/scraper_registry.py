# scraper_registry.py
from typing import Dict, Type, Optional, List, Any
from dataclasses import dataclass, field
from datetime import date
import logging
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import sys
from enum import Enum, auto
from api.scrapers.scraper_base import (
    StudioScraperStrategy,
    StudioScraperError,
    StudioConnectionError,
    StudioAvailability
)

logger = logging.getLogger(__name__)

class ScraperStatus(Enum):
    """スクレイパーの状態を表す列挙型"""
    ACTIVE = auto()
    DISABLED = auto()
    ERROR = auto()

@dataclass
class ScraperMetadata:
    """スクレイパーのメタデータ情報"""
    description: str
    version: str
    requires_auth: bool = False
    base_url: Optional[str] = None
    status: ScraperStatus = ScraperStatus.ACTIVE
    error_message: Optional[str] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """メタデータを辞書形式に変換"""
        return {
            "description": self.description,
            "version": self.version,
            "requires_auth": self.requires_auth,
            "base_url": self.base_url,
            "status": self.status.name,
            "error_message": self.error_message,
            "additional_info": self.additional_info
        }

class ScraperLoadError(Exception):
    """スクレイパーの読み込み時に発生するエラー"""
    pass

class ScraperLoader:
    """スクレイパーモジュールのローダー"""
    
    @staticmethod
    def validate_scraper_class(scraper_class: Type[StudioScraperStrategy]) -> None:
        """スクレイパークラスが必要なインターフェースを実装しているか検証"""
        required_methods = ['establish_connection', 'fetch_available_times']
        
        for method in required_methods:
            if not hasattr(scraper_class, method):
                raise ScraperLoadError(
                    f"スクレイパークラスに必要なメソッド '{method}' が実装されていません"
                )

    @classmethod
    def load_scraper_module(cls, file_path: Path) -> Any:
        """単一のスクレイパーモジュールを読み込む"""
        try:
            spec = spec_from_file_location(file_path.stem, file_path)
            if not spec or not spec.loader:
                raise ScraperLoadError(f"モジュール仕様の読み込みに失敗: {file_path}")
                
            module = module_from_spec(spec)
            sys.modules[file_path.stem] = module
            spec.loader.exec_module(module)
            
            if not hasattr(module, "register"):
                raise ScraperLoadError(
                    f"モジュール {file_path.stem} に register 関数が実装されていません"
                )
                
            return module
            
        except Exception as e:
            raise ScraperLoadError(f"モジュール {file_path} の読み込みに失敗: {str(e)}")

class ScraperRegistry:
    """スタジオスクレイパーのレジストリ"""
    
    def __init__(self):
        """レジストリの初期化"""
        self._strategies: Dict[str, Type[StudioScraperStrategy]] = {}
        self._instances: Dict[str, StudioScraperStrategy] = {}
        self._metadata: Dict[str, ScraperMetadata] = {}
        
    def register_strategy(
        self,
        studio_id: str,
        strategy_class: Type[StudioScraperStrategy],
        metadata: ScraperMetadata
    ) -> None:
        """新しいスクレイパーストラテジーを登録
        
        Args:
            studio_id: スタジオの識別子
            strategy_class: スクレイパーの実装クラス
            metadata: スクレイパーのメタデータ
        
        Raises:
            ValueError: 無効な入力の場合
            ScraperLoadError: スクレイパーの検証に失敗した場合
        """
        if not isinstance(metadata, ScraperMetadata):
            raise ValueError("メタデータはScraperMetadataのインスタンスである必要があります")

        try:
            # スクレイパークラスの検証
            ScraperLoader.validate_scraper_class(strategy_class)
            
            # インスタンス作成テスト
            instance = strategy_class()
            
            # 登録
            self._strategies[studio_id] = strategy_class
            self._instances[studio_id] = instance
            self._metadata[studio_id] = metadata
            
            logger.info(f"スクレイパー {studio_id} を登録しました")
            
        except Exception as e:
            metadata.status = ScraperStatus.ERROR
            metadata.error_message = str(e)
            self._metadata[studio_id] = metadata
            logger.error(f"スクレイパー {studio_id} の登録に失敗: {e}")
            raise ScraperLoadError(f"スクレイパー {studio_id} の登録に失敗しました") from e

    def unregister_strategy(self, studio_id: str) -> None:
        """スクレイパーストラテジーの登録を解除"""
        if studio_id in self._strategies:
            self._strategies.pop(studio_id)
            self._instances.pop(studio_id)
            self._metadata.pop(studio_id)
            logger.info(f"スクレイパー {studio_id} の登録を解除しました")

    def get_strategy(self, studio_id: str) -> StudioScraperStrategy:
        """指定されたスタジオのスクレイパーインスタンスを取得"""
        if studio_id not in self._instances:
            raise ValueError(f"未登録のスタジオです: {studio_id}")
            
        metadata = self._metadata[studio_id]
        if metadata.status != ScraperStatus.ACTIVE:
            raise StudioScraperError(
                f"スクレイパーは現在利用できません。状態: {metadata.status.name}"
            )
            
        return self._instances[studio_id]

    def get_metadata(self, studio_id: str) -> Optional[ScraperMetadata]:
        """指定されたスタジオのメタデータを取得"""
        return self._metadata.get(studio_id)

    def list_registered_studios(self) -> Dict[str, dict]:
        """登録済みの全スタジオ情報を取得"""
        return {
            studio_id: {
                "class": strategy_class.__name__,
                "metadata": self._metadata[studio_id].to_dict()
            }
            for studio_id, strategy_class in self._strategies.items()
        }

    def disable_strategy(self, studio_id: str, reason: str = "") -> None:
        """スクレイパーを一時的に無効化"""
        if studio_id in self._metadata:
            metadata = self._metadata[studio_id]
            metadata.status = ScraperStatus.DISABLED
            metadata.error_message = reason
            logger.info(f"スクレイパー {studio_id} を無効化しました: {reason}")

    def enable_strategy(self, studio_id: str) -> None:
        """無効化されたスクレイパーを再有効化"""
        if studio_id in self._metadata:
            metadata = self._metadata[studio_id]
            metadata.status = ScraperStatus.ACTIVE
            metadata.error_message = None
            logger.info(f"スクレイパー {studio_id} を再有効化しました")

class AvailabilityService:
    """スタジオの空き状況を取得するサービスクラス"""
    
    def __init__(self):
        self._registry = ScraperRegistry()

    def initialize_scrapers(self, scraper_dir: Optional[Path] = None) -> None:
        """利用可能なスクレイパーを登録
        
        Args:
            scraper_dir: スクレイパーモジュールのディレクトリパス
                        指定がない場合は現在のディレクトリを使用
        """
        if scraper_dir is None:
            scraper_dir = Path(__file__).parent

        logger.info(f"スクレイパーの初期化を開始: {scraper_dir}")
        
        for file in scraper_dir.glob("scraper_*.py"):
            if file.stem in ["scraper_base", "scraper_registry"]:
                continue
                
            try:
                module = ScraperLoader.load_scraper_module(file)
                module.register(self._registry)
                logger.info(f"スクレイパーモジュール {file.stem} を読み込みました")
                
            except ScraperLoadError as e:
                logger.error(f"スクレイパーの読み込みに失敗: {e}")
            except Exception as e:
                logger.error(f"予期せぬエラー: {e}")

    def get_availability(
        self,
        studio_id: str,
        target_date: date,
        shop_id: Optional[str] = None
    ) -> List[StudioAvailability]:
        """指定されたスタジオの空き状況を取得"""
        scraper = self._registry.get_strategy(studio_id)
        
        try:
            scraper.establish_connection(shop_id)
            return scraper.fetch_available_times(target_date)
        except Exception as e:
            logger.error(f"空き状況の取得に失敗: {e}")
            raise StudioConnectionError(f"{studio_id}の空き状況取得に失敗しました") from e

    def get_availability_json(
        self,
        studio_id: str,
        target_date: date,
        shop_id: Optional[str] = None
    ) -> str:
        """指定されたスタジオの空き状況をJSON形式で取得"""
        availabilities = self.get_availability(studio_id, target_date, shop_id)
        return self._registry.get_strategy(studio_id).to_json(availabilities)

    def list_supported_studios(self) -> Dict[str, dict]:
        """対応している全スタジオの情報を取得"""
        return self._registry.list_registered_studios()