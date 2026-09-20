import os
import warnings

ENV_FILE_PATH = os.path.join(os.path.dirname(__file__), "../../../.env")

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
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER",""),
    "password": os.getenv("DB_PASSWORD",""),
    "database": os.getenv("DB_NAME", ""),
    "charset": "utf8mb4",
}

host_ip = DB_CONFIG["host"]
user_value = DB_CONFIG["user"]
password_value = DB_CONFIG["password"]
database_name = DB_CONFIG["database"]

DB_URL = f"mysql+pymysql://{user_value}:{password_value}@{host_ip}/{database_name}?charset=utf8mb4"

# Youtube Data API
# youtube_api_key = ''
youtube_api_key = os.getenv("YOUTUBE_API_KEY", "")
# Naver Datalab
naver_client_id = os.getenv("NAVER_CLIENT_ID", "")
naver_client_secret = os.getenv("NAVER_CLIENT_SECRET", "")
naver_openapi_url = "https://openapi.naver.com/v1/datalab/search"

# Gemini (필요없을 시 삭제)
gemini_api_key = os.getenv("GEMINI_API_KEY", "")

# Apify-X
apify_api_key = os.getenv("APIFY_API_KEY", "")