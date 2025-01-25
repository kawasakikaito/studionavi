import pytest
from datetime import date, time
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup
from api.scrapers.scraper_padstudio import PadStudioScraper
from api.scrapers.scraper_base import StudioAvailability, StudioTimeSlot

@pytest.fixture
def scraper():
    return PadStudioScraper()

@pytest.fixture
def mock_session():
    return Mock()

def test_establish_connection_success(scraper, mock_session):
    """接続確立の成功テスト"""
    scraper.session = mock_session
    mock_response = Mock()
    mock_response.text = "dummy content"
    mock_session.get.return_value = mock_response
    
    result = scraper.establish_connection()
    assert result is True
    mock_session.get.assert_called_once()

def test_establish_connection_failure(scraper, mock_session):
    """接続失敗のテスト"""
    scraper.session = mock_session
    mock_session.get.side_effect = Exception("Connection error")
    
    with pytest.raises(Exception):
        scraper.establish_connection()

def test_parse_html_success(scraper):
    """HTMLパースの成功テスト"""
    html_content = "<html><body>test</body></html>"
    result = scraper._parse_html(html_content)
    assert isinstance(result, BeautifulSoup)
    assert result.find("body").text == "test"

def test_parse_html_failure(scraper):
    """HTMLパースの失敗テスト"""
    with pytest.raises(Exception):
        scraper._parse_html("invalid html")

def test_extract_time_slots(scraper):
    """時間枠抽出のテスト"""
    html = """
    <table class="table_base">
        <tr>
            <td class="item_base">10:00 ~ 11:00</td>
            <td class="item_base">11:00 ~ 12:00</td>
        </tr>
    </table>
    """
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')
    
    result = scraper._extract_time_slots(table)
    assert len(result) == 2
    assert result[0] == (time(10, 0), time(11, 0))
    assert result[1] == (time(11, 0), time(12, 0))

def test_extract_studio_info(scraper):
    """スタジオ情報抽出のテスト"""
    html = """
    <tr>
        <td>Studio A</td>
        <td class="koma"></td>
        <td class="koma"></td>
    </tr>
    """
    soup = BeautifulSoup(html, 'html.parser')
    row = soup.find('tr')
    time_slots = [(time(10, 0), time(11, 0)), (time(11, 0), time(12, 0))]
    target_date = date(2025, 1, 25)
    
    result = scraper._extract_studio_info(row, time_slots, target_date)
    assert result is not None
    assert result.room_name == "Studio A"
    assert len(result.time_slots) == 1
    assert result.time_slots[0].start_time == time(10, 0)
    assert result.time_slots[0].end_time == time(12, 0)

def test_create_studio_availability(scraper):
    """StudioAvailability生成のテスト"""
    time_slots = [
        StudioTimeSlot(start_time=time(10, 0), end_time=time(12, 0))
    ]
    target_date = date(2025, 1, 25)
    
    result = scraper._create_studio_availability(
        "Studio A",
        target_date,
        time_slots
    )
    
    assert result.room_name == "Studio A"
    assert result.date == target_date
    assert result.start_minutes == [0]
    assert result.allows_thirty_minute_slots is False
    assert len(result.time_slots) == 1

@patch('api.scrapers.scraper_padstudio.requests.Session')
def test_fetch_available_times_success(MockSession, scraper):
    """予約可能時間取得の成功テスト"""
    mock_response = Mock()
    mock_response.text = """
    <form name="form1">
        <table class="table_base">
            <tr>
                <td class="item_base">10:00 ~ 11:00</td>
            </tr>
            <tr>
                <td>Studio A</td>
                <td class="koma"></td>
            </tr>
        </table>
    </form>
    """
    MockSession.return_value.post.return_value = mock_response
    
    target_date = date(2025, 1, 25)
    result = scraper.fetch_available_times(target_date)
    
    assert len(result) == 1
    assert result[0].room_name == "Studio A"

def test_register_function():
    """スクレイパー登録関数のテスト"""
    mock_registry = Mock()
    from api.scrapers.scraper_padstudio import register
    
    register(mock_registry)
    
    mock_registry.register_strategy.assert_called_once()
    args = mock_registry.register_strategy.call_args[0]
    assert args[0] == 'pad_studio'
    assert args[1] == PadStudioScraper
    assert args[2].description == "PADスタジオ予約システム用スクレイパー"
