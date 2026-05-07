import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from env import load_env
from extract.fetch_data import FootballDataExtractor, SEASON_ID_MAP
from transform.transform_data import FootballDataTransformer
from db import get_connection
from load.load_data import FootballDataLoader
from logs.logger import get_logger

logger = get_logger(__name__)

_SEASON_LABEL = {str(v): str(k) for k, v in SEASON_ID_MAP.items()}
_WORKERS = 4
_BATCH_SIZE = 10


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int)
    parser.add_argument("--matchweek", type=int)
    parser.add_argument("--env", help="Environment to load (e.g. 'dev' loads .env.dev; omit for .env)")
    parser.add_argument(
        "--only",
        choices=["load", "enrich"],
        help="Run only the load or enrich phase (default: both)",
    )
    args = parser.parse_args()
    if args.only != "enrich" and args.season is None:
        parser.error("--season is required unless --only enrich")
    load_env(args.env)

    fetcher = FootballDataExtractor()
    transformer = FootballDataTransformer()

    if args.only != "enrich":
        if args.matchweek is not None:
            _load_gameweek(fetcher, transformer, args.season, args.matchweek)
        else:
            _load_season(fetcher, transformer, args.season)

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

    _process_matches(fetcher, transformer, raw.get("data", []))


def _load_season(
    fetcher: FootballDataExtractor,
    transformer: FootballDataTransformer,
    season: int,
) -> None:
    matches = fetcher.fetch_matches_by_season_data(season)
    if not matches:
        return

    logger.info(f"Season {season}: fetched {len(matches)} matches from API")

    with get_connection() as conn:
        FootballDataLoader(conn).load_raw("matches_by_season", str(season), matches)

    _process_matches(fetcher, transformer, matches)

    season_id_in_db = int(matches[0]["season"])
    with get_connection() as conn:
        count = FootballDataLoader(conn).get_match_count_by_season(season_id_in_db)
    logger.info(f"Season {season}: {count} matches now in DB")


def _preload_shared_dims(matches: list[dict]) -> None:
    competitions: dict = {}
    seasons: dict = {}
    clubs: dict = {}
    for m in matches:
        cid = m["competitionId"]
        if cid not in competitions:
            competitions[cid] = {"id": cid, "name": m["competition"]}
        sid = m["season"]
        if sid not in seasons:
            seasons[sid] = {"id": sid, "label": _SEASON_LABEL.get(str(sid), str(sid))}
        for side in ("homeTeam", "awayTeam"):
            team = m[side]
            tid = team["id"]
            if tid not in clubs:
                clubs[tid] = {"id": tid, "name": team["name"], "shortName": team.get("shortName")}
    with get_connection() as conn:
        loader = FootballDataLoader(conn)
        for comp in competitions.values():
            loader.load_competition(comp)
        for season in seasons.values():
            loader.load_season(season)
        for club in clubs.values():
            loader.load_club(club)


def _process_matches(
    fetcher: FootballDataExtractor,
    transformer: FootballDataTransformer,
    matches: list[dict],
) -> None:
    if not matches:
        return
    _preload_shared_dims(matches)
    for i in range(0, len(matches), _BATCH_SIZE):
        batch = matches[i:i + _BATCH_SIZE]
        logger.info(f"Processing matches {i + 1}–{i + len(batch)} of {len(matches)}")
        with ThreadPoolExecutor(max_workers=_WORKERS) as executor:
            futures = {
                executor.submit(_process_match, fetcher, transformer, match): match
                for match in batch
            }
            for future in as_completed(futures):
                match = futures[future]
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Failed to process match {match.get('matchId')}: {e}")


def _process_match(
    fetcher: FootballDataExtractor,
    transformer: FootballDataTransformer,
    match: dict,
) -> None:
    match_id = int(match["matchId"])

    with get_connection() as conn:
        FootballDataLoader(conn).load_match(_build_match_record(match))

    # Fetch from API with no DB connection held
    raw_lineups = fetcher.fetch_match_lineups_data(match_id)
    raw_events = fetcher.fetch_match_events_data(match_id)

    with get_connection() as conn:
        loader = FootballDataLoader(conn)
        if raw_lineups:
            loader.load_raw("match_lineups", match_id, raw_lineups)
            _seed_players_from_lineup(loader, raw_lineups)
            _seed_managers_from_lineup(loader, raw_lineups)
            # Lineups first — seeds dim.player rows needed for FK constraints on events
            loader.load_match_lineup(transformer.transform_match_lineup(match_id, raw_lineups))
            loader.load_match_manager(transformer.transform_match_managers(match_id, raw_lineups))
        if raw_events:
            loader.load_raw("match_events", match_id, raw_events)
            loader.load_match_events(match_id, transformer.transform_match_events(match_id, raw_events))


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
        "ground": match.get("ground"),
        "attendance": match.get("attendance"),
        "period": match.get("period"),
        "home_half_time_score": match["homeTeam"].get("halfTimeScore"),
        "away_half_time_score": match["awayTeam"].get("halfTimeScore"),
    }



def _enrich_players(
    fetcher: FootballDataExtractor,
    transformer: FootballDataTransformer,
) -> None:
    with get_connection() as conn:
        loader = FootballDataLoader(conn)
        known_seasons = loader.get_season_ids()
        known_competitions = loader.get_competition_ids()
        known_clubs = loader.get_club_ids()
        player_ids = loader.get_unenriched_player_ids()

    with ThreadPoolExecutor(max_workers=_WORKERS) as executor:
        futures = {
            executor.submit(
                _enrich_player, fetcher, transformer,
                player_id, known_seasons, known_competitions, known_clubs,
            ): player_id
            for player_id in player_ids
        }
        for future in as_completed(futures):
            player_id = futures[future]
            try:
                future.result()
            except Exception as e:
                logger.error(f"Failed to enrich player {player_id}: {e}")


def _enrich_player(
    fetcher: FootballDataExtractor,
    transformer: FootballDataTransformer,
    player_id: int,
    known_seasons: set[int],
    known_competitions: set[int],
    known_clubs: set[int],
) -> None:
    raw = fetcher.fetch_player_data(player_id)
    if not raw:
        return
    with get_connection() as conn:
        loader = FootballDataLoader(conn)
        loader.load_raw("player", player_id, raw)
        player, player_seasons = transformer.transform_player(raw)
        loader.load_player(player)
        for ps in player_seasons:
            if (
                int(ps["season_id"]) in known_seasons
                and int(ps["competition_id"]) in known_competitions
                and int(ps["team_id"]) in known_clubs
            ):
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


def _seed_managers_from_lineup(loader: FootballDataLoader, raw_lineups: dict) -> None:
    for side in ("home_team", "away_team"):
        for manager in raw_lineups.get(side, {}).get("managers", []):
            if manager.get("type") == "Manager":
                first = manager.get("firstName", "")
                last = manager.get("lastName", "")
                loader.load_manager({
                    "id": int(manager["id"]),
                    "first_name": first,
                    "last_name": last,
                    "display_name": f"{first} {last}".strip(),
                })


if __name__ == "__main__":
    main()
