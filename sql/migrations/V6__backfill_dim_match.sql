-- matches_by_season stores payload as a JSON array
INSERT INTO dim.match (id, season_id, competition_id, home_team_id, away_team_id, kickoff, matchweek, home_score, away_score)
SELECT
    (m->>'matchId')::INTEGER,
    (m->>'season')::INTEGER,
    (m->>'competitionId')::INTEGER,
    (m->'homeTeam'->>'id')::INTEGER,
    (m->'awayTeam'->>'id')::INTEGER,
    (m->>'kickoff')::TIMESTAMP,
    (m->>'phase')::INTEGER,
    (m->'homeTeam'->>'score')::INTEGER,
    (m->'awayTeam'->>'score')::INTEGER
FROM raw.api_response, jsonb_array_elements(payload) AS m
WHERE endpoint = 'matches_by_season'

UNION ALL

-- matches_by_gameweek stores payload as {"data": [...], "pagination": {...}}
SELECT
    (m->>'matchId')::INTEGER,
    (m->>'season')::INTEGER,
    (m->>'competitionId')::INTEGER,
    (m->'homeTeam'->>'id')::INTEGER,
    (m->'awayTeam'->>'id')::INTEGER,
    (m->>'kickoff')::TIMESTAMP,
    (m->>'phase')::INTEGER,
    (m->'homeTeam'->>'score')::INTEGER,
    (m->'awayTeam'->>'score')::INTEGER
FROM raw.api_response, jsonb_array_elements(payload->'data') AS m
WHERE endpoint = 'matches_by_gameweek'

ON CONFLICT DO NOTHING;
