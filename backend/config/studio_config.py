from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class ScraperConfig:
    """スクレイピング関連の設定のみを管理"""
    scraper_type: str  # "pad_studio" や "studiol" などのスクレイパー識別子
    shop_id: Optional[str]  # 店舗ID（オプショナル）

@dataclass
class StudioConfig:
    """スタジオの基本情報とスクレイピング設定を管理"""
    id: int  # データベースのプライマリーキー
    name: str  # スタジオ名
    scraper: ScraperConfig  # スクレイピング設定

# スタジオの設定
STUDIO_CONFIGS: Dict[str, StudioConfig] = {
    "1": StudioConfig(
        id=1,
        name="PADstudio",
        scraper=ScraperConfig(
            scraper_type="pad_studio",
            shop_id=None,
        ),
    ),
    "2": StudioConfig(
        id=2,
        name="ベースオントップ アメ村店",
        scraper=ScraperConfig(
            scraper_type="studiol",
            shop_id="673",
        ),
    ),
    "3": StudioConfig(
        id=3,
        name="グリーンスタジオ",
        scraper=ScraperConfig(
            scraper_type="studiol",
            shop_id="546",
        ),
    )
}