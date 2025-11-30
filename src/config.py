from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

MODEL_DIR = DATA_DIR / "model"
DATABASE_FILE = DATA_DIR / "database" / "images.duckdb"
