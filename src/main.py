from extract.fetch_data import FootballDataFetcher

def main():
    print("main...")

    fetcher = FootballDataFetcher()
    data = fetcher.fetch_player_data()
    print(data)


if __name__ == "__main__":
    main()