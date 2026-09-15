import os
import warnings

# .env 파일 경로: backend/server/.env
ENV_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")


def _load_env_file(path: str) -> None:
    """
    .env 파일을 읽어 os.environ에 주입한다.
    이미 시스템 환경변수로 설정돼 있다면 덮어쓰지 않는다.
    """
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
    """필수 환경변수가 없으면 서버 기동 시점에 바로 에러를 낸다."""
    value = os.getenv(key)
    if not value:
        raise RuntimeError(
            f"환경변수 '{key}'가 설정되지 않았습니다. "
            f"backend/server/.env 파일에 {key}=값 형태로 추가해주세요."
        )
    return value


_load_env_file(ENV_FILE_PATH)

# 경고창 숨기기 설정
warnings.filterwarnings("ignore", category=UserWarning)

# ── 데이터베이스 설정 ─────────────────────────────
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": _require_env("DB_PASSWORD"),
    "database": os.getenv("DB_NAME", "viralfinder"),
    "charset": "utf8mb4",
}

host_ip = DB_CONFIG["host"]
user_value = DB_CONFIG["user"]
password_value = DB_CONFIG["password"]
database_name = DB_CONFIG["database"]

DB_URL = f"mysql+pymysql://{user_value}:{password_value}@{host_ip}/{database_name}?charset=utf8mb4"

# ── 외부 API 키 ───────────────────────────────────
# Youtube Data API
youtube_api_key = _require_env("YOUTUBE_API_KEY")

# Naver Datalab
naver_client_id = _require_env("NAVER_CLIENT_ID")
naver_client_secret = _require_env("NAVER_CLIENT_SECRET")
naver_openapi_url = "https://openapi.naver.com/v1/datalab/search"

# Gemini (필요없을 시 .env에서 빼도 됨 -> 선택값이라 필수 체크 안 함)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_api_key = GEMINI_API_KEY

# Apify-X
apify_api_key = _require_env("APIFY_API_KEY")