import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_ROOT = os.path.dirname(CURRENT_DIR)
BACKEND_ROOT = os.path.dirname(SERVER_ROOT)

if BACKEND_ROOT not in sys.path:
    sys.path.append(BACKEND_ROOT)

from datetime import datetime, timedelta
import json
import logging
import subprocess
from fastapi import FastAPI, HTTPException
import pandas as pd
import redis
import pymysql

from server.config.database import fetch_data
from server.config.config import DB_CONFIG
from server.analyzer.analyzer import analyze_viral_traffic

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI()

rd = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

def ensure_keyword_exists(keyword_name):
    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            cursor.execute("INSERT IGNORE INTO keyword (target_keyword) VALUES (%s);", (keyword_name,))
            conn.commit()
            cursor.execute("SELECT keyword_id FROM keyword WHERE target_keyword = %s;", (keyword_name,))
            result = cursor.fetchone()
            return result[0] if result else None
    finally:
        conn.close()

def run_crawling(keyword):
    logging.info(f"네이버 크롤링 시작")
    naver_path = os.path.join(SERVER_ROOT, "crawling", "naver_data_lab_crawling.py")
    subprocess.run([sys.executable, naver_path, keyword], text=True, encoding='utf-8', cwd=SERVER_ROOT)

    logging.info(f"구글 크롤링 시작")
    google_path = os.path.join(SERVER_ROOT, "crawling", "pytrends_crawling.py")
    subprocess.run([sys.executable, google_path, keyword], text=True, encoding='utf-8', cwd=SERVER_ROOT)

@app.get("/api/analysis/{keyword}")
async def get_trend_analysis(keyword: str):
    keyword = keyword.strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="키워드를 입력해주세요.")

    current_time = datetime.now()

    try:
        cached_json = rd.get(keyword)

        if cached_json:
            cached_data = json.loads(cached_json)
            updated_at = datetime.strptime(cached_data["updated_at"], "%Y-%m-%d %H:%M:%S")

            is_date_changed = current_time.date() != updated_at.date()
            is_expired_6hours = (current_time - updated_at) > timedelta(hours=6)

            if not is_date_changed and not is_expired_6hours:
                logging.info(f"🔥 [Cache Hit] '{keyword}' 데이터가 유효하므로 캐시에서 즉시 반환합니다.")
                return cached_data

        logging.info(f"❄️ [Cache Miss] '{keyword}' 데이터가 없거나 만료되어 새로 수집을 시작합니다.")

        inserted_id = ensure_keyword_exists(keyword)
        logging.info(f"🔑 부모 키워드 등록 완료 (keyword_id: {inserted_id})")

        run_crawling(keyword)

        trend_df, video_df, keyword_id = fetch_data(keyword)

        if keyword_id is None or trend_df.empty:
            logging.warning(f"⚠️ 키워드 '{keyword}'에 대한 필수 트렌드 데이터가 수집되지 않았습니다.")
            raise HTTPException(status_code=404, detail="데이터 수집에 실패했습니다.")

        if video_df is None or video_df.empty:
            video_df = pd.DataFrame(columns=["video_id", "uploaded_date", "view_count"])

        result_df = analyze_viral_traffic(trend_df, video_df)

        if isinstance(result_df, pd.DataFrame):
            statistical_analysis = json.loads(result_df.to_json(orient="records", date_format="iso"))
        elif isinstance(result_df, dict):
            statistical_analysis = json.loads(pd.Series(result_df).to_json(date_format="iso"))
        else:
            statistical_analysis = result_df

        final_api_response = {
            "status": "success",
            "keyword_id": keyword_id,
            "keyword_name": keyword,
            "updated_at": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "statistics": statistical_analysis,
            "ai_evaluation": "ai_report_dict"
        }

        serialized_json = json.dumps(final_api_response, ensure_ascii=False)
        rd.set(keyword, serialized_json)
        logging.info(f"💾 [Cache Save] '{keyword}' 분석 결과가 Redis 캐시에 저장되었습니다.")

        return final_api_response

    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"❌ 분석 파이프라인 가동 중 실패: {e}")
        raise HTTPException(status_code=500, detail=f"서버 내부 에러: {e}")

def main(keyword):
    import asyncio
    return asyncio.run(get_trend_analysis(keyword))

if __name__ == "__main__":
    user_input = input("분석할 키워드를 입력하세요: ").strip()
    if user_input:
        res = main(user_input)
        print(json.dumps(res, indent=4, ensure_ascii=False))