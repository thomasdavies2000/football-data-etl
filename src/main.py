from extract.fetch_data import FootballDataFetcher
from transform.transform_data import FootballDataTransformer

def main():
    print("main...")

    fetcher = FootballDataFetcher()
    player_data = fetcher.fetch_player_data(1803)
    print("Raw playerdata:", player_data)


if __name__ == "__main__":
    main()