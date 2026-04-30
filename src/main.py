import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from env import load_env
from extract.fetch_data import FootballDataExtractor, SEASON_ID_MAP
from transform.transform_data import FootballDataTransformer
from db import get_connection
from load.load_data import FootballDataLoader

# Inverse of SEASON_ID_MAP: API season ID (str) -> calendar year (str) for display
_SEASON_LABEL = {str(v): str(k) for k, v in SEASON_ID_MAP.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--matchweek", type=int)
    parser.add_argument("--env", help="Environment to load (e.g. 'dev' loads .env.dev; omit for .env)")
    parser.add_argument(
        "--only",
        choices=["load", "enrich"],
        help="Run only the load or enrich phase (default: both)",
    )
    args = parser.parse_args()
    load_env(args.env)

    if args.season not in SEASON_ID_MAP and args.matchweek is None:
        parser.error("--matchweek is required for seasons not in SEASON_ID_MAP")

    fetcher = FootballDataExtractor()
    transformer = FootballDataTransformer()

    if args.only != "enrich":
        if args.season in SEASON_ID_MAP:
            _load_season(fetcher, transformer, args.season)
        else:
            _load_gameweek(fetcher, transformer, args.season, args.matchweek)

    if args.only != "load":
        _enrich_players(fetcher, transformer)


def _load_gameweek(
    fetcher: FootballDataExtractor,
    transformer: FootballDataTransformer,
    season: int,
    matchweek: int,
) -> None:
    raw = fetcher.fetch_matches_by_gameweek_data(season, matchweek)
    if not raw:
        return

    with get_connection() as conn:
        FootballDataLoader(conn).load_raw("matches_by_gameweek", f"{season}_{matchweek}", raw)

    for match in raw.get("data", []):
        with get_connection() as conn:
            loader = FootballDataLoader(conn)
            loader.load_competition({"id": match["competitionId"], "name": match["competition"]})
            loader.load_season({"id": match["season"], "label": match["season"]})

            for side in ("homeTeam", "awayTeam"):
                team = match[side]
                loader.load_club({"id": team["id"], "name": team["name"], "shortName": team.get("shortName")})

            loader.load_match(_build_match_record(match))
            _load_match(fetcher, transformer, loader, int(match["matchId"]))


def _load_season(
    fetcher: FootballDataExtractor,
    transformer: FootballDataTransformer,
    season: int,
) -> None:
    matches = fetcher.fetch_matches_by_season_data(season)
    if not matches:
        return

    with get_connection() as conn:
        FootballDataLoader(conn).load_raw("matches_by_season", str(season), matches)

    for match in matches:
        with get_connection() as conn:
            loader = FootballDataLoader(conn)
            loader.load_competition({"id": match["competitionId"], "name": match["competition"]})
            season_id = match["season"]
            loader.load_season({"id": season_id, "label": _SEASON_LABEL.get(season_id, season_id)})

            for side in ("homeTeam", "awayTeam"):
                team = match[side]
                loader.load_club({"id": team["id"], "name": team["name"], "shortName": team.get("shortName")})

            loader.load_match(_build_match_record(match))
            _load_match(fetcher, transformer, loader, int(match["matchId"]))


def _build_match_record(match: dict) -> dict:
    return {
        "id": int(match["matchId"]),
        "season_id": int(match["season"]),
        "competition_id": int(match["competitionId"]),
        "home_team_id": int(match["homeTeam"]["id"]),
        "away_team_id": int(match["awayTeam"]["id"]),
        "kickoff": match.get("kickoff"),
        "matchweek": int(match["phase"]) if match.get("phase") else None,
        "home_score": match["homeTeam"].get("score"),
        "away_score": match["awayTeam"].get("score"),
    }


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


def _enrich_players(
    fetcher: FootballDataExtractor,
    transformer: FootballDataTransformer,
) -> None:
    with get_connection() as conn:
        loader = FootballDataLoader(conn)
        known_seasons = loader.get_season_ids()
        player_ids = loader.get_unenriched_player_ids()

    for player_id in player_ids:
        raw = fetcher.fetch_player_data(player_id)
        if not raw:
            continue
        with get_connection() as conn:
            loader = FootballDataLoader(conn)
            loader.load_raw("player", player_id, raw)
            player, player_seasons = transformer.transform_player(raw)
            loader.load_player(player)
            for ps in player_seasons:
                if int(ps["season_id"]) in known_seasons:
                    loader.load_player_season(ps)


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
