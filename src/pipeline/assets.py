from dagster import asset, AssetExecutionContext, StaticPartitionsDefinition

from extract.fetch_data import FootballDataExtractor
from transform.transform_data import FootballDataTransformer
from main import _load_season, _enrich_players

SEASON_PARTITIONS = StaticPartitionsDefinition([str(y) for y in range(2000, 2026)])


@asset(partitions_def=SEASON_PARTITIONS)
def season_data(context: AssetExecutionContext) -> None:
    season = int(context.partition_key)
    context.log.info(f"Loading season {season}")
    _load_season(FootballDataExtractor(), FootballDataTransformer(), season)


@asset(deps=[season_data])
def enriched_players(context: AssetExecutionContext) -> None:
    context.log.info("Enriching unenriched players")
    _enrich_players(FootballDataExtractor(), FootballDataTransformer())
