import requests

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