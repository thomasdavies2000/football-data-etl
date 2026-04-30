from dagster import Definitions
from .assets import season_data, enriched_players

defs = Definitions(assets=[season_data, enriched_players])
