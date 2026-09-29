import os
import warnings

ENV_FILE_PATH = os.path.join(os.path.dirname(__file__), "../.env")

def _load_env_file(path: str) -> None:
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            os.environ.setdefault(key, value)

def _require_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(
            f"환경변수 '{key}'가 설정되지 않았습니다. "
        )
    return value

_load_env_file(ENV_FILE_PATH)

# 경고창 숨기기 설정
warnings.filterwarnings("ignore", category=UserWarning)

# 데이터베이스 설정
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": _require_env("DB_PASSWORD"),
    "database": os.getenv("DB_NAME", "viral_finder"),
    "charset": "utf8mb4",
}

host_ip = DB_CONFIG["host"]
user_value = DB_CONFIG["user"]
password_value = DB_CONFIG["password"]
database_name = DB_CONFIG["database"]

DB_URL = f"mysql+pymysql://{user_value}:{password_value}@{host_ip}/{database_name}?charset=utf8mb4"

# Youtube Data API
youtube_api_key = _require_env("YOUTUBE_API_KEY")
# Naver Datalab
naver_client_id = _require_env("NAVER_CLIENT_ID")
naver_client_secret = _require_env("NAVER_CLIENT_SECRET")
naver_openapi_url = "https://openapi.naver.com/v1/datalab/search"

# Gemini (필요없을 시 삭제)
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Apify-X
apify_api_key = _require_env("APIFY_API_KEY")