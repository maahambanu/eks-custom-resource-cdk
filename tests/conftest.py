import sys
from pathlib import Path


lambda_path = Path(__file__).resolve().parents[1] / "lambda"

sys.path.insert(0, str(lambda_path))