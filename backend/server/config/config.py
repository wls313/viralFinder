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
# 주의: 이전 버전은 여기 값이 비어 있어 SyntaxError가 발생해 백엔드 전체가
# import 시점에 죽는 상태였습니다. 반드시 backend/server/.env 파일에
# DB_HOST / DB_USER / DB_PASSWORD / DB_NAME 값을 채워주세요.
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "1234"),
    "database": os.getenv("DB_NAME", "viralfinder"),
    "charset": "utf8mb4",
}

host_ip = DB_CONFIG["host"]
user_value = DB_CONFIG["user"]
password_value = DB_CONFIG["password"]
database_name = DB_CONFIG["database"]

# 유튜브 api 키
# 주의: 기존에 실제 키 값이 소스코드에 하드코딩된 채 public 저장소에 커밋되어
# 있었습니다. .env로 옮겼으니, 기존에 노출됐던 키는 반드시 재발급(rotate) 받으세요.
youtube_api_key = os.getenv("YOUTUBE_API_KEY", "")

# 네이버 데이터랩
naver_client_id = os.getenv("NAVER_CLIENT_ID", "")
naver_client_secret = os.getenv("NAVER_CLIENT_SECRET", "")
naver_openapi_url = "https://openapi.naver.com/v1/datalab/search"