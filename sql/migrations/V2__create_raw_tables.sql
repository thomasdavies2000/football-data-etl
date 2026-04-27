CREATE TABLE raw.api_response (
    id          SERIAL PRIMARY KEY,
    endpoint    TEXT        NOT NULL,
    entity_id   TEXT        NOT NULL,
    fetched_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    payload     JSONB       NOT NULL
);
