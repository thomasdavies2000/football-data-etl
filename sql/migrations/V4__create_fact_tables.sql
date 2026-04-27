CREATE TABLE fact.player_season (
    player_id       INTEGER NOT NULL REFERENCES dim.player(player_id),
    season_id       INTEGER NOT NULL REFERENCES dim.season(id),
    competition_id  INTEGER NOT NULL REFERENCES dim.competition(id),
    club_id         INTEGER REFERENCES dim.club(id),
    position        TEXT,
    shirt_num       INTEGER,
    height          INTEGER,
    weight          INTEGER,
    loan            BOOLEAN,
    joined_club     DATE,
    PRIMARY KEY (player_id, season_id, competition_id)
);

-- Goals, cards, and substitutions flattened into a single table.
-- event_type: 'goal' | 'card' | 'sub'
CREATE TABLE fact.match_event (
    id              SERIAL  PRIMARY KEY,
    match_id        INTEGER NOT NULL,
    team_id         INTEGER REFERENCES dim.club(id),
    event_type      TEXT    NOT NULL,
    player_id       INTEGER REFERENCES dim.player(player_id),
    period          TEXT,
    time            INTEGER,
    occurred_at     TIMESTAMPTZ,
    -- goal-specific
    goal_type       TEXT,
    assist_player_id INTEGER  REFERENCES dim.player(player_id),
    -- card-specific
    card_type       TEXT,
    -- sub-specific
    player_off_id   INTEGER  REFERENCES dim.player(player_id)
);

CREATE TABLE fact.match_lineup (
    match_id    INTEGER NOT NULL,
    team_id     INTEGER REFERENCES dim.club(id),
    player_id   INTEGER REFERENCES dim.player(player_id),
    is_starter  BOOLEAN NOT NULL,
    shirt_num   INTEGER,
    position    TEXT,
    PRIMARY KEY (match_id, team_id, player_id)
);
