from datetime import datetime

from logs.logger import get_logger

logger = get_logger(__name__)


def _parse_timestamp(ts: str | None) -> datetime | None:
    if not ts:
        return None
    return datetime.strptime(ts, "%Y%m%dT%H%M%S%z")


class FootballDataTransformer:

    def transform_player(self, raw_data: list) -> tuple[dict, list[dict]]:
        """Transform raw player API response into a player dimension and season rows.

        Returns:
            (player_dict, list of player_season dicts)
        """
        first = raw_data[0]

        player = {
            "player_id": first["id"]["playerId"],
            "first_name": first["name"]["first"],
            "last_name": first["name"]["last"],
            "display_name": first["name"]["display"],
            "date_of_birth": first["dates"]["birth"],
            "country": first["country"]["country"],
            "country_iso": first["country"]["isoCode"],
        }

        player_seasons = [
            {
                "player_id": entry["id"]["playerId"],
                "season_id": entry["id"]["seasonId"],
                "competition_id": entry["id"]["competitionId"],
                "team_id": entry["team"]["id"],
                "team_name": entry["team"]["name"],
                "position": entry["position"],
                "shirt_num": entry.get("shirtNum"),
                "height": entry.get("height"),
                "weight": entry.get("weight"),
                "loan": entry["team"].get("loan", 0),
                "joined_club": entry["dates"].get("joinedClub"),
            }
            for entry in raw_data
        ]

        return player, player_seasons

    def transform_match_events(self, match_id: int, raw_data: dict) -> list[dict]:
        events = []

        for side in ("homeTeam", "awayTeam"):
            team = raw_data.get(side, {})
            team_id = int(team["id"])

            for goal in team.get("goals", []):
                if not goal.get("playerId"):
                    logger.warning(f"match {match_id}: goal missing playerId")
                events.append({
                    "match_id": match_id,
                    "team_id": team_id,
                    "event_type": "goal",
                    "player_id": int(goal["playerId"]) if goal.get("playerId") else None,
                    "period": goal.get("period"),
                    "time": int(goal["time"]) if goal.get("time") else None,
                    "occurred_at": _parse_timestamp(goal.get("timestamp")),
                    "goal_type": goal.get("goalType"),
                    "assist_player_id": int(goal["assistPlayerId"]) if goal.get("assistPlayerId") else None,
                    "card_type": None,
                    "player_off_id": None,
                })

            for card in team.get("cards", []):
                if not card.get("playerId"):
                    logger.warning(f"match {match_id}: card missing playerId")
                events.append({
                    "match_id": match_id,
                    "team_id": team_id,
                    "event_type": "card",
                    "player_id": int(card["playerId"]) if card.get("playerId") else None,
                    "period": card.get("period"),
                    "time": int(card["time"]) if card.get("time") else None,
                    "occurred_at": _parse_timestamp(card.get("timestamp")),
                    "goal_type": None,
                    "assist_player_id": None,
                    "card_type": card.get("type"),
                    "player_off_id": None,
                })

            for sub in team.get("subs", []):
                if not sub.get("playerOnId"):
                    logger.warning(f"match {match_id}: sub missing playerOnId")
                if not sub.get("playerOffId"):
                    logger.warning(f"match {match_id}: sub missing playerOffId")
                events.append({
                    "match_id": match_id,
                    "team_id": team_id,
                    "event_type": "sub",
                    "player_id": int(sub["playerOnId"]) if sub.get("playerOnId") else None,
                    "period": sub.get("period"),
                    "time": int(sub["time"]) if sub.get("time") else None,
                    "occurred_at": _parse_timestamp(sub.get("timestamp")),
                    "goal_type": None,
                    "assist_player_id": None,
                    "card_type": None,
                    "player_off_id": int(sub["playerOffId"]) if sub.get("playerOffId") else None,
                })

        return events

    def transform_match_lineup(self, match_id: int, raw_data: dict) -> list[dict]:
        rows = []

        for side in ("home_team", "away_team"):
            team = raw_data.get(side, {})
            team_id = int(team["teamId"])

            for player in team.get("players", []):
                rows.append({
                    "match_id": match_id,
                    "team_id": team_id,
                    "player_id": int(player["id"]),
                    "is_starter": player["position"] != "Substitute",
                    "shirt_num": int(player["shirtNum"]) if player.get("shirtNum") else None,
                    "position": player.get("position"),
                })

        return rows

    def transform_match_managers(self, match_id: int, raw_data: dict) -> list[dict]:
        rows = []

        for side in ("home_team", "away_team"):
            team = raw_data.get(side, {})
            team_id = int(team["teamId"])

            for manager in team.get("managers", []):
                if manager.get("type") == "Manager":
                    rows.append({
                        "match_id": match_id,
                        "team_id": team_id,
                        "manager_id": int(manager["id"]),
                    })

        return rows
