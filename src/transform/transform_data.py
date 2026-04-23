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
