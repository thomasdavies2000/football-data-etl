from datetime import datetime


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
                events.append({
                    "match_id": match_id,
                    "team_id": team_id,
                    "event_type": "goal",
                    "player_id": int(goal["playerId"]),
                    "period": goal.get("period"),
                    "time": int(goal["time"]) if goal.get("time") else None,
                    "occurred_at": _parse_timestamp(goal.get("timestamp")),
                    "goal_type": goal.get("goalType"),
                    "assist_player_id": int(goal["assistPlayerId"]) if goal.get("assistPlayerId") else None,
                    "card_type": None,
                    "player_off_id": None,
                })

            for card in team.get("cards", []):
                events.append({
                    "match_id": match_id,
                    "team_id": team_id,
                    "event_type": "card",
                    "player_id": int(card["playerId"]),
                    "period": card.get("period"),
                    "time": int(card["time"]) if card.get("time") else None,
                    "occurred_at": _parse_timestamp(card.get("timestamp")),
                    "goal_type": None,
                    "assist_player_id": None,
                    "card_type": card.get("type"),
                    "player_off_id": None,
                })

            for sub in team.get("subs", []):
                events.append({
                    "match_id": match_id,
                    "team_id": team_id,
                    "event_type": "sub",
                    "player_id": int(sub["playerOnId"]),
                    "period": sub.get("period"),
                    "time": int(sub["time"]) if sub.get("time") else None,
                    "occurred_at": _parse_timestamp(sub.get("timestamp")),
                    "goal_type": None,
                    "assist_player_id": None,
                    "card_type": None,
                    "player_off_id": int(sub["playerOffId"]),
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
