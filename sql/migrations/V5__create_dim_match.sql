CREATE TABLE dim.match (
    id              INTEGER PRIMARY KEY,
    season_id       INTEGER NOT NULL REFERENCES dim.season(id),
    competition_id  INTEGER NOT NULL REFERENCES dim.competition(id),
    home_team_id    INTEGER REFERENCES dim.club(id),
    away_team_id    INTEGER REFERENCES dim.club(id),
    kickoff         TIMESTAMP,
    matchweek       INTEGER,
    home_score      INTEGER,
    away_score      INTEGER
);
