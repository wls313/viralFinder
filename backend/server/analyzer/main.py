import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_ROOT = os.path.dirname(CURRENT_DIR)
BACKEND_ROOT = os.path.dirname(SERVER_ROOT)

if BACKEND_ROOT not in sys.path:
    sys.path.append(BACKEND_ROOT)

from fastapi import FastAPI, HTTPException
import pandas as pd
import redis
import pymysql

from server.config.database import fetch_data
from server.config.config import DB_CONFIG
from server.analyzer.analyzer import analyze_viral_traffic
from server.services.crawler_service import run_sequential_crawling

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI()

# Redis 연결 세팅
rd = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

CACHE_EXPIRE_HOURS = 6
LOCK_TIMEOUT = 180

def ensure_keyword_id(keyword_name: str):
    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            cursor.execute("INSERT IGNORE INTO keyword (target_keyword) VALUES (%s);", (keyword_name,))
            conn.commit()
            cursor.execute("SELECT keyword_id FROM keyword WHERE target_keyword = %s;", (keyword_name,))
            row = cursor.fetchone()
            return row[0] if row else None
    finally:
        conn.close()


def save_tweets(keyword_id: int, tweets: list):
    if not tweets or not keyword_id:
        return

    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            query = """
                    INSERT IGNORE INTO x_tweet 
                (tweet_id, keyword_id, full_text, screen_name, user_id, favorite_count, retweet_count, view_count, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s); \
                    """
            for tweet in tweets:
                raw_views = tweet.get("views", 0)
                views = int(raw_views) if isinstance(raw_views, int) or (isinstance(raw_views, str) and raw_views.isdigit()) else 0

                cursor.execute(query, (
                    str(tweet.get("id")),
                    keyword_id,
                    tweet.get("content"),
                    tweet.get("screen_name", "unknown"),
                    tweet.get("user_id", 0),
                    tweet.get("likes", 0),
                    tweet.get("retweets", 0),
                    views,
                    datetime.now()
                ))
            conn.commit()
            logging.info(f"x_tweet DB 저장 완료: {len(tweets)}건")
    except Exception as e:
        logging.error(f"x_tweet DB 저장 실패: {e}")
    finally:
        conn.close()


@app.get("/api/analysis/{keyword}")
async def get_trend_analysis(keyword: str):
    keyword = keyword.strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="키워드를 입력해주세요.")

    now = datetime.now()
    lock_key = f"lock:analysis:{keyword}"

    # 캐시 체크
    cached = rd.get(keyword)
    if cached:
        cached_data = json.loads(cached)
        updated_at = datetime.strptime(cached_data["updated_at"], "%Y-%m-%d %H:%M:%S")

        # 날짜가 같고 6시간 이내라면 캐시 반환
        if now.date() == updated_at.date() and (now - updated_at) <= timedelta(hours=CACHE_EXPIRE_HOURS):
            logging.info(f"[Cache Hit] '{keyword}' 데이터 반환")
            return cached_data

    logging.info(f"[Cache Miss] '{keyword}' 신규 크롤링 진행")

    # 동시 요청 방지를 위한 분산 락
    ac_lock = rd.set(lock_key, "locked", nx=True, ex=LOCK_TIMEOUT)

    if not ac_lock:
        logging.info(f"'{keyword}' 선행 작업 진행 중. 캐시 생성 대기...")
        wait_limit = 120
        interval = 2
        elapsed = 0

        while elapsed < wait_limit:
            time.sleep(interval)
            elapsed += interval

            cached = rd.get(keyword)
            if cached:
                logging.info(f"[Wait Success] '{keyword}' 캐시 생성 완료 확인")
                return json.loads(cached)

        raise HTTPException(status_code=530, detail="수집 작업 대기 시간이 초과되었습니다.")

    # 크롤링 및 데이터 분석 수행
    try:
        keyword_id = ensure_keyword_id(keyword)

        x_tweets = run_sequential_crawling(keyword)

        save_tweets(keyword_id, x_tweets)

        fetch_result = fetch_data(keyword)
        trend_df = fetch_result[0] if isinstance(fetch_result, tuple) else fetch_result
        db_keyword_id = fetch_result[2] if isinstance(fetch_result, tuple) and len(fetch_result) > 2 else keyword_id

        if trend_df is None or (isinstance(trend_df, pd.DataFrame) and trend_df.empty):
            logging.warning(f"'{keyword}' 트렌드 데이터 수집 실패")
            raise HTTPException(status_code=404, detail="트렌드 데이터를 찾을 수 없습니다.")

        trend_summary = analyze_viral_traffic(trend_df)

        # API 응답
        response_data = {
            "status": "success",
            "keyword_id": db_keyword_id,
            "keyword_name": keyword,
            "updated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "trends": trend_summary,
            "twitter_trends": x_tweets
        }

        # 4. Redis 캐시 저장 (TTL: 6시간)
        serialized = json.dumps(response_data, ensure_ascii=False)
        rd.setex(name=keyword, time=timedelta(hours=CACHE_EXPIRE_HOURS), value=serialized)
        logging.info(f"[Cache Saved] '{keyword}' 캐시 저장 완료")

        return response_data

    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"분석 파이프라인 오류: {e}")
        raise HTTPException(status_code=500, detail=f"서버 에러: {e}")

    finally:
        # 작업 완료 후 락 해제
        rd.delete(lock_key)


def main(keyword):
    import asyncio
    return asyncio.run(get_trend_analysis(keyword))


if __name__ == "__main__":
    user_input = input("분석할 키워드를 입력하세요: ").strip()
    if user_input:
        res = main(user_input)
        print(json.dumps(res, indent=4, ensure_ascii=False))