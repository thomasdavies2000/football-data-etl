import os
from dotenv import load_dotenv


def load_env(env: str | None) -> None:
    root = os.path.join(os.path.dirname(__file__), "..")
    filename = f".env.{env}" if env else ".env"
    path = os.path.join(root, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Environment file not found: {path}")
    load_dotenv(path)
