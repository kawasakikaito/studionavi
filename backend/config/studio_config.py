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
    ),
    "4": StudioConfig(
        id=4,
        name="ベースオントップ 梅田店",
        scraper=ScraperConfig(
            scraper_type="studiol",
            shop_id="671",
        ),
    ),
    "5": StudioConfig(
        id=5,
        name="ベースオントップ 心斎橋",
        scraper=ScraperConfig(
            scraper_type="studiol",
            shop_id="682",
        ),
    ),
    # Studio246の店舗を追加
    "6": StudioConfig(
        id=6,
        name="Studio246 OSAKA",
        scraper=ScraperConfig(
            scraper_type="studio246",
            shop_id="08",  # 大阪・梅田
        ),
    ),
    "7": StudioConfig(
        id=7,
        name="Studio246 JUSO",
        scraper=ScraperConfig(
            scraper_type="studio246",
            shop_id="11",  # 大阪・十三
        ),
    ),
    "8": StudioConfig(
        id=8,
        name="Studio246 NAMBA",
        scraper=ScraperConfig(
            scraper_type="studio246",
            shop_id="09",  # 大阪・なんば
        ),
    ),
    "9": StudioConfig(
        id=9,
        name="Studio246 WEST",
        scraper=ScraperConfig(
            scraper_type="studio246",
            shop_id="05",  # 神戸・三宮
        ),
    ),
    "10": StudioConfig(
        id=10,
        name="Studio246 KYOTO",
        scraper=ScraperConfig(
            scraper_type="studio246",
            shop_id="06",  # 京都・大宮
        ),
    ),
    "11": StudioConfig(
        id=11,
        name="Studio246 NAGOYA",
        scraper=ScraperConfig(
            scraper_type="studio246",
            shop_id="07",  # 名古屋・東山
        ),
    ),
    "12": StudioConfig(
        id=12,
        name="ベースオントップ 京橋店",
        scraper=ScraperConfig(
            scraper_type="studiol",
            shop_id="654",
        ),
    ),
}