import requests
from logs.logger import get_logger

logger = get_logger(__name__)

class FootballDataFetcher:

    base_url = "https://sdp-prem-prod.premier-league-prod.pulselive.com/"

    def __init__(self):
        pass

    def fetch_player_data(self, id) -> list | None: 
        players_url = f"{self.base_url}/api/v2/players/{id}"
        
        print(f"Fetching football data from {players_url}...")

        # make the API call and return the data
        try:
            response = requests.get(players_url)
            if response.status_code == 200:
                return response.json()
            else:            
                print(f"Failed to fetch data: {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            print("Request timed out")
            return None
        except requests.exceptions.ConnectionError:
            print("Failed to connect to the server")
            return None
        except requests.exceptions.RequestException as e:
            print(f"An unexpected error occurred: {e}")
            return None
        
    def fetch_match_events_data(self, id) -> dict | None:
        
        match_events_url = f"{self.base_url}/api/v1/matches/{id}/events"
        print(f"Fetching football data from {match_events_url}...")

        # make the API call and return the data
        try:
            response = requests.get(match_events_url)
            if response.status_code == 200:
                return response.json()
            else:            
                print(f"Failed to fetch data: {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            print("Request timed out")
            return None
        except requests.exceptions.ConnectionError:
            print("Failed to connect to the server")
            return None
        except requests.exceptions.RequestException as e:
            print(f"An unexpected error occurred: {e}")
            return None
        
    def fetch_match_lineups_data(self, id) -> dict | None:
        
        match_lineups_url = f"{self.base_url}/api/v3/matches/{id}/lineups"
        print(f"Fetching football data from {match_lineups_url}...")

        # make the API call and return the data
        try:
            response = requests.get(match_lineups_url)
            if response.status_code == 200:
                return response.json()
            else:            
                print(f"Failed to fetch data: {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            print("Request timed out")
            return None
        except requests.exceptions.ConnectionError:
            print("Failed to connect to the server")
            return None
        except requests.exceptions.RequestException as e:
            print(f"An unexpected error occurred: {e}")
            return None
        
    def fetch_club_data(self, id) -> dict | None:
        
        clubs_url = f"{self.base_url}/api/v1/metadata/SDP_FOOTBALL_TEAM/{id}"
        print(f"Fetching football data from {clubs_url}...")

        # make the API call and return the data
        try:
            response = requests.get(clubs_url)
            if response.status_code == 200:
                return response.json()
            else:            
                print(f"Failed to fetch data: {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            print("Request timed out")
            return None
        except requests.exceptions.ConnectionError:
            print("Failed to connect to the server")
            return None
        except requests.exceptions.RequestException as e:
            print(f"An unexpected error occurred: {e}")
            return None
