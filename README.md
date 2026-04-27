# football-data-etl

An ETL pipeline that extracts Premier League data from the Premier League SDP API and loads it into a PostgreSQL database.

## Project structure

```
src/
├── extract/      # API fetch layer
├── transform/    # Data transformation
├── load/         # Database load layer (in progress)
└── quality/      # Data quality checks

sql/
└── migrations/   # Flyway versioned migrations

logs/             # Logging config
tests/            # Unit tests with fixtures
```

Based on: https://medium.com/@aliakbarhosseinzadeh/structuring-an-etl-pipeline-project-best-practices-5ed1e4d5a601

## Local setup

Copy `.env.example` to `.env`, then:

```bash
docker compose up
```

This starts PostgreSQL and runs all Flyway migrations in order. Flyway exits once migrations are applied; Postgres stays running.

To reset the database and re-run all migrations from scratch:

```bash
docker compose down -v
docker compose up
```

## Design decisions

### Database: PostgreSQL

PostgreSQL is the target database. All schema, migration, and load layer code targets Postgres specifically.

### Migrations: Flyway

Schema changes are managed as versioned SQL migration files in `sql/migrations/`, following Flyway's `V{n}__{description}.sql` naming convention. Flyway runs as a Docker service on startup and applies any pending migrations before exiting.

### Schema layout

Three Postgres schemas separate concerns:

| Schema | Purpose |
|--------|---------|
| `raw`  | Raw API responses stored as JSONB — replay buffer if transform logic changes |
| `dim`  | Dimension tables: slowly-changing reference data (players, clubs, seasons, competitions) |
| `fact` | Fact tables: high-cardinality, time-bound data (player seasons, match events, lineups) |

This follows a **star schema** pattern, with dimension tables as the reference core and fact tables recording what happened.

### Primary keys: API integers

All ID columns use `INTEGER`, casting the API's string IDs (e.g. `"1803"`) on load. This was chosen over:

- **TEXT PKs** — slower index lookups, risk of duplicate rows from formatting differences (e.g. `"1803"` vs `"01803"`)
- **Surrogate keys (SERIAL + UNIQUE api_id)** — adds mapping complexity that isn't warranted when the API IDs are stable integer sequences

### match_event: single table with event_type discriminator

Goals, cards, and substitutions are stored in one `fact.match_event` table with an `event_type` column (`'goal'`, `'card'`, `'sub'`), rather than three separate tables. Event-specific fields (`goal_type`, `card_type`, `assist_player_id`, `player_off_id`) are nullable and only populated for the relevant event type. This simplifies querying across all match events.

### Load strategy: upsert

All loads use `INSERT ... ON CONFLICT DO UPDATE`, making every pipeline run idempotent. Re-running the pipeline for a player or match that's already been loaded will update in place rather than duplicate rows.

### Insert order

FK constraints mean dimensions must be populated before facts. Within that, the API is ID-driven — you need an entity's ID before you can fetch its related data — so the natural fetch and insert order is:

1. `dim.competition` — seed with known competition IDs
2. `dim.season` — seed with known season IDs
3. `dim.club` — fetch club metadata by ID
4. `dim.player` — discovered via club squad endpoints; insert player identity records
5. `fact.player_season` — loaded alongside player data; requires player, season, competition, and club to exist
6. `fact.match_event` — fetched per match ID; requires club and player records to exist
7. `fact.match_lineup` — fetched per match ID; requires club and player records to exist

`raw.api_response` can be written at any point — it has no FK dependencies and should be written before transformation so the raw payload is always persisted regardless of whether the transform/load succeeds.

### Foreign keys

All fact tables reference dimension tables via FK constraints, so referential integrity is enforced at the database level.

### Data quality

Unexpected nulls in the transform layer (e.g. a card with no `playerId`) are logged as warnings. `assistPlayerId` being null is not flagged — it is expected, since not all goals have an assist.

## Potential improvements

### Persistent quality issue tracking

Currently data quality problems are surfaced as log warnings. A more robust approach would be a dedicated `quality.issues` table:

```sql
CREATE TABLE quality.issues (
    id          SERIAL PRIMARY KEY,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    entity_type TEXT NOT NULL,  -- 'match_event', 'lineup', etc.
    entity_id   TEXT NOT NULL,  -- match_id or other identifier
    field       TEXT NOT NULL,  -- the field that failed
    issue       TEXT NOT NULL   -- human-readable description
);
```

The transform layer would write a row here instead of (or in addition to) logging, making quality issues queryable and persistent across runs.
