import requests
from logs.logger import get_logger

logger = get_logger(__name__)

# Some early seasons use an opaque numeric ID in the API rather than the calendar year.
SEASON_ID_MAP = {
    1992: 11,
    1993: 12,
    1994: 13,
}


class FootballDataExtractor:

    base_url = "https://sdp-prem-prod.premier-league-prod.pulselive.com/"

    def __init__(self):
        pass

    def fetch_player_data(self, id) -> list | None: 
        players_url = f"{self.base_url}/api/v2/players/{id}"
        
        logger.info(f"Fetching football data from {players_url}...")

        # make the API call and return the data
        try:
            response = requests.get(players_url)
            if response.status_code == 200:
                return response.json()
            else:            
                logger.error(f"Failed to fetch data: {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            logger.error("Request timed out")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to the server")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"An unexpected error occurred: {e}")
            return None
        
    def fetch_matches_by_gameweek_data(self, season, matchweek, competition=8) -> list | None:
        # example url: https://sdp-prem-prod.premier-league-prod.pulselive.com/api/v2/matches?competition=8&season=2025&matchweek=34&_limit=20
        # another example, for some reason this is 1992/1993: https://sdp-prem-prod.premier-league-prod.pulselive.com/api/v2/matches?competition=8&season=11
        # https://sdp-prem-prod.premier-league-prod.pulselive.com/api/v2/matches?competition=8&season=11&kickoff%3E1992-08-01&kickoff%3C1992-09-01&_limit=20&_next=MTY3ODA
        season = SEASON_ID_MAP.get(season, season)
        matches_by_gameweek_url = f"{self.base_url}/api/v2/matches?competition={competition}&season={season}&matchweek={matchweek}&_limit=20"
        logger.info(f"Fetching football data from {matches_by_gameweek_url}...")

        # make the API call and return the data
        try:
            response = requests.get(matches_by_gameweek_url)
            if response.status_code == 200:
                return response.json()
            else:            
                logger.error(f"Failed to fetch data: {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            logger.error("Request timed out")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to the server")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"An unexpected error occurred: {e}")
            return None
                
    def fetch_matches_by_season_data(self, season, competition=8) -> list | None:
        season_id = SEASON_ID_MAP.get(season, season)
        base = f"{self.base_url}/api/v2/matches?competition={competition}&season={season_id}&_limit=20"

        all_matches = []
        next_cursor = None

        while True:
            url = f"{base}&_next={next_cursor}" if next_cursor else base
            logger.info(f"Fetching football data from {url}...")
            try:
                response = requests.get(url)
                if response.status_code != 200:
                    logger.error(f"Failed to fetch data: {response.status_code}")
                    return None
                page = response.json()
            except requests.exceptions.Timeout:
                logger.error("Request timed out")
                return None
            except requests.exceptions.ConnectionError:
                logger.error("Failed to connect to the server")
                return None
            except requests.exceptions.RequestException as e:
                logger.error(f"An unexpected error occurred: {e}")
                return None

            all_matches.extend(page.get("data", []))
            next_cursor = page.get("pagination", {}).get("_next")
            if not next_cursor:
                break

        return all_matches

    def fetch_match_events_data(self, id) -> dict | None:
        
        match_events_url = f"{self.base_url}/api/v1/matches/{id}/events"
        logger.info(f"Fetching football data from {match_events_url}...")

        # make the API call and return the data
        try:
            response = requests.get(match_events_url)
            if response.status_code == 200:
                return response.json()
            else:            
                logger.error(f"Failed to fetch data: {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            logger.error("Request timed out")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to the server")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"An unexpected error occurred: {e}")
            return None
        
    def fetch_match_lineups_data(self, id) -> dict | None:
        
        match_lineups_url = f"{self.base_url}/api/v3/matches/{id}/lineups"
        logger.info(f"Fetching football data from {match_lineups_url}...")

        # make the API call and return the data
        try:
            response = requests.get(match_lineups_url)
            if response.status_code == 200:
                return response.json()
            else:            
                logger.error(f"Failed to fetch data: {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            logger.error("Request timed out")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to the server")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"An unexpected error occurred: {e}")
            return None
        
    def fetch_club_data(self, id) -> dict | None:
        
        clubs_url = f"{self.base_url}/api/v1/metadata/SDP_FOOTBALL_TEAM/{id}"
        logger.info(f"Fetching football data from {clubs_url}...")

        # make the API call and return the data
        try:
            response = requests.get(clubs_url)
            if response.status_code == 200:
                return response.json()
            else:            
                logger.error(f"Failed to fetch data: {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            logger.error("Request timed out")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to the server")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"An unexpected error occurred: {e}")
            return None
        
    def fetch_club_squad_data(self, id, season, competition=8) -> dict | None:
        # example url https://sdp-prem-prod.premier-league-prod.pulselive.com/api/v2/competitions/8/seasons/2010/teams/43/squad
        season = SEASON_ID_MAP.get(season, season)
        club_squad_url = f"{self.base_url}/api/v2/competitions/{competition}/seasons/{season}/teams/{id}/squad"
        logger.info(f"Fetching football data from {club_squad_url}...")

        # make the API call and return the data
        try:
            response = requests.get(club_squad_url)
            if response.status_code == 200:
                return response.json()
            else:            
                logger.error(f"Failed to fetch data: {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            logger.error("Request timed out")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to the server")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"An unexpected error occurred: {e}")
            return None
