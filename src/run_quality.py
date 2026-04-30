import argparse
import sys

from env import load_env
from db import get_connection
from quality import QualityChecker, Status

parser = argparse.ArgumentParser()
parser.add_argument("--env", help="Environment to load (e.g. 'dev' loads .env.dev; omit for .env)")
args = parser.parse_args()

load_env(args.env)

with get_connection() as conn:
    results = QualityChecker(conn).run_all()

if any(r.status == Status.FAIL for r in results):
    sys.exit(1)
