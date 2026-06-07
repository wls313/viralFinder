import os
import warnings

ENV_FILE_PATH = os.path.join(os.path.dirname(__file__), ".env")

if os.path.exists(ENV_FILE_PATH):
    with open(ENV_FILE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 경고창 숨기기 설정
warnings.filterwarnings("ignore", category=UserWarning)

# 데이터베이스 설정
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "1234",
    "database": "viralFinder",
    "charset": "utf8mb4",
}