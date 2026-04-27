CREATE TABLE dim.competition (
    id      TEXT PRIMARY KEY,
    name    TEXT
);

CREATE TABLE dim.season (
    id      TEXT PRIMARY KEY,
    label   TEXT
);

CREATE TABLE dim.club (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    short_name  TEXT
);

CREATE TABLE dim.player (
    player_id       TEXT PRIMARY KEY,
    first_name      TEXT,
    last_name       TEXT,
    display_name    TEXT NOT NULL,
    date_of_birth   DATE,
    country         TEXT,
    country_iso     TEXT
);
