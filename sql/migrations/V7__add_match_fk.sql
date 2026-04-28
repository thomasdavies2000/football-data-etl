ALTER TABLE fact.match_event
    ADD CONSTRAINT match_event_match_id_fkey FOREIGN KEY (match_id) REFERENCES dim.match(id);

ALTER TABLE fact.match_lineup
    ADD CONSTRAINT match_lineup_match_id_fkey FOREIGN KEY (match_id) REFERENCES dim.match(id);
