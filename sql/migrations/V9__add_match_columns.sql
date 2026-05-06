ALTER TABLE dim.match
    ADD COLUMN ground               TEXT,
    ADD COLUMN attendance           INTEGER,
    ADD COLUMN period               TEXT,
    ADD COLUMN home_half_time_score INTEGER,
    ADD COLUMN away_half_time_score INTEGER;
