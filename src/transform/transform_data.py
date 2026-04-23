class FootballDataTransformer:

    def transform_player(self, raw_data: list) -> dict:
        """Extract a flat dict from raw player API response, suitable for DB insertion."""
        return {
            "id": raw_data.get("id"),
            "first_name": raw_data.get("name", {}).get("first"),
            "last_name": raw_data.get("name", {}).get("last"),
            "display_name": raw_data.get("name", {}).get("display"),
            "date_of_birth": raw_data.get("birth", {}).get("date", {}).get("millis"),
            "country": raw_data.get("birth", {}).get("country", {}).get("country"),
            "position": raw_data.get("info", {}).get("position"),
            "shirt_num": raw_data.get("info", {}).get("shirtNum"),
        }
