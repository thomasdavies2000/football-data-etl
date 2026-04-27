import json

from logs.logger import get_logger

logger = get_logger(__name__)


class FootballDataLoader:

    def __init__(self, conn):
        self.conn = conn

    def load_raw(self, endpoint: str, entity_id: str | int, payload: dict | list) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO raw.api_response (endpoint, entity_id, payload)
                VALUES (%s, %s, %s)
                """,
                (endpoint, str(entity_id), json.dumps(payload)),
            )
        logger.info(f"Stored raw response for {endpoint}/{entity_id}")

    def load_competition(self, competition: dict) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO dim.competition (id, name)
                VALUES (%(id)s, %(name)s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name
                """,
                {"id": int(competition["id"]), "name": competition.get("name")},
            )
        logger.info(f"Upserted competition {competition['id']}")

    def load_season(self, season: dict) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO dim.season (id, label)
                VALUES (%(id)s, %(label)s)
                ON CONFLICT (id) DO UPDATE SET
                    label = EXCLUDED.label
                """,
                {"id": int(season["id"]), "label": season.get("label")},
            )
        logger.info(f"Upserted season {season['id']}")

    def load_club(self, club: dict) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO dim.club (id, name, short_name)
                VALUES (%(id)s, %(name)s, %(short_name)s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    short_name = EXCLUDED.short_name
                """,
                {
                    "id": int(club["id"]),
                    "name": club["name"],
                    "short_name": club.get("shortName"),
                },
            )
        logger.info(f"Upserted club {club['id']}")

    def load_player(self, player: dict) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO dim.player (
                    player_id, first_name, last_name, display_name,
                    date_of_birth, country, country_iso
                )
                VALUES (
                    %(player_id)s, %(first_name)s, %(last_name)s, %(display_name)s,
                    %(date_of_birth)s, %(country)s, %(country_iso)s
                )
                ON CONFLICT (player_id) DO UPDATE SET
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    display_name = EXCLUDED.display_name,
                    date_of_birth = EXCLUDED.date_of_birth,
                    country = EXCLUDED.country,
                    country_iso = EXCLUDED.country_iso
                """,
                {
                    "player_id": int(player["player_id"]),
                    "first_name": player.get("first_name"),
                    "last_name": player.get("last_name"),
                    "display_name": player["display_name"],
                    "date_of_birth": player.get("date_of_birth") or None,
                    "country": player.get("country"),
                    "country_iso": player.get("country_iso"),
                },
            )
        logger.info(f"Upserted player {player['player_id']}")

    def load_player_season(self, player_season: dict) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO fact.player_season (
                    player_id, season_id, competition_id, club_id,
                    position, shirt_num, height, weight, loan, joined_club
                )
                VALUES (
                    %(player_id)s, %(season_id)s, %(competition_id)s, %(club_id)s,
                    %(position)s, %(shirt_num)s, %(height)s, %(weight)s, %(loan)s, %(joined_club)s
                )
                ON CONFLICT (player_id, season_id, competition_id) DO UPDATE SET
                    club_id = EXCLUDED.club_id,
                    position = EXCLUDED.position,
                    shirt_num = EXCLUDED.shirt_num,
                    height = EXCLUDED.height,
                    weight = EXCLUDED.weight,
                    loan = EXCLUDED.loan,
                    joined_club = EXCLUDED.joined_club
                """,
                {
                    "player_id": int(player_season["player_id"]),
                    "season_id": int(player_season["season_id"]),
                    "competition_id": int(player_season["competition_id"]),
                    "club_id": int(player_season["team_id"]),
                    "position": player_season.get("position"),
                    "shirt_num": player_season.get("shirt_num"),
                    "height": player_season.get("height"),
                    "weight": player_season.get("weight"),
                    "loan": bool(player_season.get("loan", 0)),
                    "joined_club": player_season.get("joined_club") or None,
                },
            )
        logger.info(f"Upserted player season {player_season['player_id']}/{player_season['season_id']}")

    def load_match_events(self, match_id: int, events: list[dict]) -> None:
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM fact.match_event WHERE match_id = %s", (match_id,))
            for event in events:
                cur.execute(
                    """
                    INSERT INTO fact.match_event (
                        match_id, team_id, event_type, player_id, period, time, occurred_at,
                        goal_type, assist_player_id, card_type, player_off_id
                    )
                    VALUES (
                        %(match_id)s, %(team_id)s, %(event_type)s, %(player_id)s,
                        %(period)s, %(time)s, %(occurred_at)s,
                        %(goal_type)s, %(assist_player_id)s, %(card_type)s, %(player_off_id)s
                    )
                    """,
                    event,
                )
        logger.info(f"Loaded {len(events)} events for match {match_id}")

    def load_match_lineup(self, lineup_rows: list[dict]) -> None:
        if not lineup_rows:
            return
        with self.conn.cursor() as cur:
            for row in lineup_rows:
                cur.execute(
                    """
                    INSERT INTO fact.match_lineup (
                        match_id, team_id, player_id, is_starter, shirt_num, position
                    )
                    VALUES (
                        %(match_id)s, %(team_id)s, %(player_id)s,
                        %(is_starter)s, %(shirt_num)s, %(position)s
                    )
                    ON CONFLICT (match_id, team_id, player_id) DO UPDATE SET
                        is_starter = EXCLUDED.is_starter,
                        shirt_num = EXCLUDED.shirt_num,
                        position = EXCLUDED.position
                    """,
                    row,
                )
        logger.info(f"Upserted {len(lineup_rows)} lineup rows for match {lineup_rows[0]['match_id']}")
