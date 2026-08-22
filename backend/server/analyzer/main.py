import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_ROOT = os.path.dirname(CURRENT_DIR)
BACKEND_ROOT = os.path.dirname(SERVER_ROOT)

for p in [BACKEND_ROOT, SERVER_ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)

import json
import time
import logging
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
import pandas as pd
import redis
import pymysql

from server.config.database import fetch_data
from server.config.config import DB_CONFIG
from server.analyzer.analyzer import analyze_viral_traffic
from server.analyzer.crawler_service import run_sequential_crawling

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Trend Tracker Python Crawler Service")

rd = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

CACHE_EXPIRE_HOURS = 6
LOCK_TIMEOUT = 180
LOCK_WAIT_LIMIT = 120
LOCK_WAIT_INTERVAL = 2


def get_keyword_id(keyword_name: str):
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
            logger.info(f"x_tweet 저장 {len(tweets)}건")
    except Exception as e:
        logger.error(f"x_tweet 저장 실패: {e}")
    finally:
        conn.close()


def get_cached(keyword: str):
    cached = rd.get(keyword)
    if not cached:
        return None

    data = json.loads(cached)
    updated_at = datetime.strptime(data["updated_at"], "%Y-%m-%d %H:%M:%S")
    now = datetime.now()

    if now.date() == updated_at.date() and (now - updated_at) <= timedelta(hours=CACHE_EXPIRE_HOURS):
        return data
    return None


def wait_for_cache(keyword: str):
    elapsed = 0
    while elapsed < LOCK_WAIT_LIMIT:
        time.sleep(LOCK_WAIT_INTERVAL)
        elapsed += LOCK_WAIT_INTERVAL
        cached = rd.get(keyword)
        if cached:
            return json.loads(cached)
    raise HTTPException(status_code=530, detail="수집 작업 대기 시간이 초과되었습니다.")


@app.get("/api/analysis/{keyword}")
def get_trend(keyword: str):
    keyword = keyword.strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="키워드를 입력해주세요.")

    cached = get_cached(keyword)
    if cached:
        return cached

    lock_key = f"lock:analysis:{keyword}"
    acquired = rd.set(lock_key, "locked", nx=True, ex=LOCK_TIMEOUT)

    if not acquired:
        logger.info(f"'{keyword}' 선행 작업 대기")
        return wait_for_cache(keyword)

    try:
        keyword_id = get_keyword_id(keyword)
        x_tweets = run_sequential_crawling(keyword)
        save_tweets(keyword_id, x_tweets)

        fetch_result = fetch_data(keyword)
        trend_df = fetch_result[0] if isinstance(fetch_result, tuple) else fetch_result
        db_keyword_id = fetch_result[2] if isinstance(fetch_result, tuple) and len(fetch_result) > 2 else keyword_id

        if trend_df is None or (isinstance(trend_df, pd.DataFrame) and trend_df.empty):
            raise HTTPException(status_code=404, detail="트렌드 데이터를 찾을 수 없습니다.")

        trend_summary = analyze_viral_traffic(trend_df)

        response_data = {
            "status": "success",
            "keyword_id": db_keyword_id,
            "keyword_name": keyword,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "trends": trend_summary,
            "twitter_trends": x_tweets
        }

        rd.setex(keyword, timedelta(hours=CACHE_EXPIRE_HOURS), json.dumps(response_data, ensure_ascii=False))
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"분석 파이프라인 오류: {e}")
        raise HTTPException(status_code=500, detail=f"서버 에러: {e}")
    finally:
        rd.delete(lock_key)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)