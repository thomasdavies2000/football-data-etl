CREATE TABLE dim.manager (
    id           INTEGER PRIMARY KEY,
    first_name   TEXT,
    last_name    TEXT,
    display_name TEXT NOT NULL
);

CREATE TABLE fact.match_manager (
    match_id    INTEGER NOT NULL REFERENCES dim.match(id),
    team_id     INTEGER NOT NULL REFERENCES dim.club(id),
    manager_id  INTEGER NOT NULL REFERENCES dim.manager(id),
    PRIMARY KEY (match_id, team_id, manager_id)
);
