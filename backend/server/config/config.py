import os
import warnings

ENV_FILE_PATH = os.path.join(os.path.dirname(__file__), "../.env")

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
    "user":
    "password":
    "database":
    "charset": "utf8mb4",
}

host_ip = DB_CONFIG["host"]
user_value = DB_CONFIG["user"]
password_value = DB_CONFIG["password"]
database_name = DB_CONFIG["database"]

# 유튜브 api 키
youtube_api_key = 'AIzaSyCx-AlOUq3HNhSQkF0y33RX-5uDQcerEvM'

#네이버 테이터 랩
# Naver Datalab
naver_client_id = 'Or44GhFkSQ6ld3by3_tx'
naver_client_secret = '5fgc908_KF'
naver_openapi_url = "https://openapi.naver.com/v1/datalab/search"