from unittest.mock import patch, Mock
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from extract.fetch_data import FootballDataFetcher


def test_fetch_match_events_returns_dict():
    with open("tests/fixtures/matches_events_response.json") as f:
        mock_data = json.load(f)

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_data

    with patch("extract.fetch_data.requests.get", return_value=mock_response):
        fetcher = FootballDataFetcher()
        result = fetcher.fetch_match_events_data(12345)
        assert isinstance(result, dict)


def test_fetch_player_data_returns_list():
    with open("tests/fixtures/player_response.json") as f:
        mock_data = json.load(f)

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_data

    with patch("extract.fetch_data.requests.get", return_value=mock_response):
        fetcher = FootballDataFetcher()
        result = fetcher.fetch_player_data(1803)
        assert isinstance(result, list)
