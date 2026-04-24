import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from extract.fetch_data import FootballDataExtractor
from transform.transform_data import FootballDataTransformer

def main():
    print("main...")

    fetcher = FootballDataExtractor()
    player_data = fetcher.fetch_player_data(1803)
    print("Raw playerdata:", player_data)

    match_events_data = fetcher.fetch_match_events_data(17070)

    print("Raw match events data:", match_events_data)

    match_lineups_data = fetcher.fetch_match_lineups_data(17070)

    print("Raw match lineups data:", match_lineups_data)

    club_data = fetcher.fetch_club_data(43)
    print("Raw club data:", club_data)

if __name__ == "__main__":
    main()