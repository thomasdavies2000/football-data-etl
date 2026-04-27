import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv

from extract.fetch_data import FootballDataExtractor
from transform.transform_data import FootballDataTransformer
from load.db import get_connection
from load.load_data import FootballDataLoader

load_dotenv()

SEASON = 2024
MATCHWEEK = 1


def main():
    fetcher = FootballDataExtractor()
    transformer = FootballDataTransformer()

    with get_connection() as conn:
        loader = FootballDataLoader(conn)
        _load_gameweek(fetcher, transformer, loader, SEASON, MATCHWEEK)


def _load_gameweek(
    fetcher: FootballDataExtractor,
    transformer: FootballDataTransformer,
    loader: FootballDataLoader,
    season: int,
    matchweek: int,
) -> None:
    raw = fetcher.fetch_matches_by_gameweek_data(season, matchweek)
    if not raw:
        return

    loader.load_raw("matches_by_gameweek", f"{season}_{matchweek}", raw)

    for match in raw.get("data", []):
        loader.load_competition({"id": match["competitionId"], "name": match["competition"]})
        loader.load_season({"id": match["season"], "label": match["season"]})

        for side in ("homeTeam", "awayTeam"):
            team = match[side]
            loader.load_club({"id": team["id"], "name": team["name"], "shortName": team.get("shortName")})

        _load_match(fetcher, transformer, loader, int(match["matchId"]))


def _load_match(
    fetcher: FootballDataExtractor,
    transformer: FootballDataTransformer,
    loader: FootballDataLoader,
    match_id: int,
) -> None:
    # Lineups first — seeds dim.player rows needed for FK constraints on events
    raw_lineups = fetcher.fetch_match_lineups_data(match_id)
    if raw_lineups:
        loader.load_raw("match_lineups", match_id, raw_lineups)
        _seed_players_from_lineup(loader, raw_lineups)
        lineup_rows = transformer.transform_match_lineup(match_id, raw_lineups)
        loader.load_match_lineup(lineup_rows)

    raw_events = fetcher.fetch_match_events_data(match_id)
    if raw_events:
        loader.load_raw("match_events", match_id, raw_events)
        events = transformer.transform_match_events(match_id, raw_events)
        loader.load_match_events(match_id, events)


def _seed_players_from_lineup(loader: FootballDataLoader, raw_lineups: dict) -> None:
    for side in ("home_team", "away_team"):
        for player in raw_lineups.get(side, {}).get("players", []):
            first = player.get("firstName", "")
            last = player.get("lastName", "")
            loader.load_player({
                "player_id": player["id"],
                "first_name": first,
                "last_name": last,
                "display_name": f"{first} {last}".strip(),
                "date_of_birth": None,
                "country": None,
                "country_iso": None,
            })


if __name__ == "__main__":
    main()
