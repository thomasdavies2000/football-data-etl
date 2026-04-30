from dataclasses import dataclass
from enum import Enum

from logs.logger import get_logger

logger = get_logger(__name__)


class Status(Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


@dataclass
class CheckResult:
    name: str
    status: Status
    message: str


class QualityChecker:

    def __init__(self, conn):
        self.conn = conn

    def run_all(self) -> list[CheckResult]:
        results = [
            self.check_season_match_counts(),
            self.check_goal_player_ids(),
            self.check_lineup_starter_counts(),
        ]
        for r in results:
            logger.info(f"[{r.status.value}] {r.name}: {r.message}")
        return results

    def check_season_match_counts(self) -> CheckResult:
        with self.conn.cursor() as cur:
            cur.execute("""
                WITH team_counts AS (
                    SELECT season_id, competition_id, COUNT(DISTINCT team_id) AS n
                    FROM (
                        SELECT season_id, competition_id, home_team_id AS team_id FROM dim.match
                        UNION
                        SELECT season_id, competition_id, away_team_id AS team_id FROM dim.match
                    ) t
                    GROUP BY season_id, competition_id
                ),
                match_counts AS (
                    SELECT
                        season_id,
                        competition_id,
                        COUNT(*) AS actual,
                        COUNT(*) FILTER (WHERE home_score IS NULL OR away_score IS NULL) AS unscored
                    FROM dim.match
                    GROUP BY season_id, competition_id
                )
                SELECT
                    mc.season_id,
                    mc.competition_id,
                    mc.actual,
                    tc.n * (tc.n - 1) AS expected,
                    mc.unscored
                FROM match_counts mc
                JOIN team_counts tc USING (season_id, competition_id)
                ORDER BY mc.season_id, mc.competition_id
            """)
            rows = cur.fetchall()

        logger.info(f"  {len(rows)} season/competition combination(s) found")
        warnings, failures = [], []
        for season_id, competition_id, actual, expected, unscored in rows:
            logger.info(f"  season={season_id} competition={competition_id}: {actual}/{expected} matches")
            if actual == expected:
                continue
            label = f"season={season_id} competition={competition_id} (actual={actual}, expected={expected})"
            if unscored > 0:
                warnings.append(label)
            else:
                failures.append(label)

        if failures:
            return CheckResult(
                "season_match_counts",
                Status.FAIL,
                f"Match count mismatch in completed seasons: {'; '.join(failures)}",
            )
        if warnings:
            return CheckResult(
                "season_match_counts",
                Status.WARNING,
                f"Match count below expected (season likely in progress): {'; '.join(warnings)}",
            )
        return CheckResult("season_match_counts", Status.PASS, "All seasons have expected match counts")

    def check_goal_player_ids(self) -> CheckResult:
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM fact.match_event
                WHERE event_type = 'goal' AND player_id IS NULL
            """)
            missing = cur.fetchone()[0]

            cur.execute("""
                SELECT COUNT(*) FROM fact.match_event
                WHERE event_type = 'goal' AND player_id IS NOT NULL
            """)
            total = cur.fetchone()[0]

        logger.info(f"  {total} goal events, {missing} missing player_id")

        if missing:
            return CheckResult(
                "goal_player_ids",
                Status.FAIL,
                f"{missing}/{total + missing} goals have no player_id",
            )
        return CheckResult("goal_player_ids", Status.PASS, f"All {total} goals have a player_id")

    def check_lineup_starter_counts(self) -> CheckResult:
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM (
                    SELECT match_id, team_id
                    FROM fact.match_lineup
                    WHERE is_starter = TRUE
                    GROUP BY match_id, team_id
                    HAVING COUNT(*) != 11
                ) violations
            """)
            violations = cur.fetchone()[0]

            cur.execute("""
                SELECT COUNT(DISTINCT match_id) FROM fact.match_lineup
            """)
            total_matches = cur.fetchone()[0]

        logger.info(f"  {total_matches} matches checked, {violations} team lineup(s) without exactly 11 starters")

        if violations:
            return CheckResult(
                "lineup_starter_counts",
                Status.FAIL,
                f"{violations} team lineup(s) do not have exactly 11 starters",
            )
        return CheckResult("lineup_starter_counts", Status.PASS, f"All lineups across {total_matches} matches have exactly 11 starters")
