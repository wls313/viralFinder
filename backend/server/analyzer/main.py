import os
import sys
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import pymysql

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_ROOT = os.path.dirname(CURRENT_DIR)
BACKEND_ROOT = os.path.dirname(SERVER_ROOT)

for p in [BACKEND_ROOT, SERVER_ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)

from server.config.database import fetch_data
from server.config.config import DB_CONFIG
from server.analyzer.analyzer import analyze_viral_traffic
from server.analyzer.crawler_service import run_sequential_crawling
from progress_state import progress

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Trend Tracker Python Crawler Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_keyword_id(keyword_name: str):
    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT IGNORE INTO keyword (target_keyword) VALUES (%s);",
                (keyword_name,),
            )
            conn.commit()
            cursor.execute(
                "SELECT keyword_id FROM keyword WHERE target_keyword = %s;",
                (keyword_name,),
            )
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
                (tweet_id, keyword_id, full_text, screen_name, user_id,
                 favorite_count, retweet_count, view_count, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            for tweet in tweets:
                raw_views = tweet.get("views", 0)
                views = (
                    int(raw_views)
                    if isinstance(raw_views, int)
                    or (isinstance(raw_views, str) and raw_views.isdigit())
                    else 0
                )
                cursor.execute(
                    query,
                    (
                        str(tweet.get("id")),
                        keyword_id,
                        tweet.get("content"),
                        tweet.get("screen_name", "unknown"),
                        tweet.get("user_id", 0),
                        tweet.get("likes", 0),
                        tweet.get("retweets", 0),
                        views,
                        datetime.now(),
                    ),
                )
            conn.commit()
            logger.info(f"x_tweet 저장 {len(tweets)}건")
    except Exception as e:
        logger.error(f"x_tweet 저장 실패: {e}")
    finally:
        conn.close()


class KeywordRequest(BaseModel):
    keyword: str


@app.get("/progress")
async def get_progress():
    return progress


@app.get("/api/analysis/{keyword}")
def get_trend(keyword: str, period: str):
    keyword = keyword.strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="키워드를 입력해주세요.")

    try:
        keyword_id = get_keyword_id(keyword)
        results_data = run_sequential_crawling(keyword, period)

        raw_tweets = (
            results_data.get("x_trends_data", [])
            if isinstance(results_data, dict)
            else results_data
        )
        if isinstance(raw_tweets, list):
            x_tweets = raw_tweets
        elif isinstance(raw_tweets, dict):
            x_tweets = raw_tweets.get("data", raw_tweets.get("tweets", []))
        else:
            x_tweets = []

        save_tweets(keyword_id, x_tweets)

        fetch_result = fetch_data(keyword)
        trend_df = fetch_result[0] if isinstance(fetch_result, tuple) else fetch_result
        db_keyword_id = (
            fetch_result[2]
            if isinstance(fetch_result, tuple) and len(fetch_result) > 2
            else keyword_id
        )

        if trend_df is None or (
            isinstance(trend_df, pd.DataFrame) and trend_df.empty
        ):
            trend_summary = {
                "latest_naver_ratio": 0.0,
                "latest_google_ratio": 0.0,
                "short_term_avg": 0.0,
                "long_term_avg": 0.0,
                "math_prediction": "INSUFFICIENT_DATA",
            }
        else:
            trend_summary = analyze_viral_traffic(trend_df)

        naver_data_list = results_data.get("naver_data", [])
        google_data_list = results_data.get("google_data", [])

        return {
            "status": "success",
            "keyword_id": db_keyword_id,
            "keyword_name": keyword,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "trends": trend_summary,
            "twitter_trends": x_tweets,
            "naver_trend": naver_data_list,
            "google_trend": google_data_list,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"분석 파이프라인 오류: {e}")
        raise HTTPException(status_code=500, detail=f"서버 에러: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)