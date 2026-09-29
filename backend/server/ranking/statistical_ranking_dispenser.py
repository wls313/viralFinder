import pymysql, os, sys
import uvicorn

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.concurrency import run_in_threadpool

current_dir = os.path.dirname(os.path.realpath(__file__))
top_level_dir = os.path.dirname(current_dir)
if top_level_dir not in sys.path:
    sys.path.append(top_level_dir)

from progress_state import progress
from config.config import DB_CONFIG
from crawling.apify_x_crawling import search_trending_tweets
from crawling.youtube_crawling import search_recommend_videos

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

def get_db_connection():
    return pymysql.connect(host=DB_CONFIG["host"], user=DB_CONFIG["user"], password=DB_CONFIG["password"],
                           database=DB_CONFIG["database"], charset=DB_CONFIG["charset"])

@app.get("/api/rankings")
def get_trend_ranking(period: int = Query(7)):
    if period not in [7, 30, 90]:
        period = 7

    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 실시간 트렌드 - 통합 급상승 순위
            cursor.execute(f"""
                SELECT k.keyword_id, k.target_keyword, 
                       (IFNULL(k.naver_t_score_{period}, 0) + IFNULL(k.google_t_score_{period}, 0)) / 2 AS score,
                       (IFNULL(k.naver_delta_{period}, 0) + IFNULL(k.google_delta_{period}, 0)) AS delta,
                       COUNT(t.tweet_id) AS mention_count
                FROM keyword k
                LEFT JOIN x_tweet t ON k.keyword_id = t.keyword_id 
                                   AND t.created_at >= DATE_SUB(NOW(), INTERVAL {period} DAY)
                GROUP BY k.keyword_id
                ORDER BY delta DESC LIMIT 10;
            """)
            integrated_surge = cursor.fetchall()

            # 실시간 트렌드 - 통합 언급량 순위
            cursor.execute(f"""
                SELECT k.keyword_id, k.target_keyword, 
                       (IFNULL(k.naver_t_score_{period}, 0) + IFNULL(k.google_t_score_{period}, 0)) / 2 AS score,
                       (IFNULL(k.naver_delta_{period}, 0) + IFNULL(k.google_delta_{period}, 0)) AS delta,
                       COUNT(t.tweet_id) AS mention_count
                FROM keyword k
                LEFT JOIN x_tweet t ON k.keyword_id = t.keyword_id 
                                   AND t.created_at >= DATE_SUB(NOW(), INTERVAL {period} DAY)
                GROUP BY k.keyword_id
                ORDER BY mention_count DESC LIMIT 10;
            """)
            integrated_mention = cursor.fetchall()

            # 실시간 트렌드 - 네이버 급상승 순위
            cursor.execute(f"""
                SELECT k.keyword_id, k.target_keyword, 
                       k.naver_t_score_{period} AS score, 
                       k.naver_delta_{period} AS delta, 
                       COUNT(t.tweet_id) AS mention_count
                FROM keyword k
                LEFT JOIN x_tweet t ON k.keyword_id = t.keyword_id 
                                   AND t.created_at >= DATE_SUB(NOW(), INTERVAL {period} DAY)
                WHERE k.naver_delta_{period} IS NOT NULL
                GROUP BY k.keyword_id
                ORDER BY delta DESC LIMIT 10;
            """)
            naver_surge = cursor.fetchall()

            # 실시간 트렌드 - 네이버 언급량 순위
            cursor.execute(f"""
                SELECT k.keyword_id, k.target_keyword, 
                       k.naver_t_score_{period} AS score, 
                       k.naver_delta_{period} AS delta,
                       COUNT(t.tweet_id) AS mention_count
                FROM keyword k
                LEFT JOIN x_tweet t ON k.keyword_id = t.keyword_id 
                                   AND t.created_at >= DATE_SUB(NOW(), INTERVAL {period} DAY)
                WHERE k.naver_t_score_{period} IS NOT NULL
                GROUP BY k.keyword_id
                ORDER BY mention_count DESC LIMIT 10;
            """)
            naver_mention = cursor.fetchall()

            # 실시간 트렌드 - 구글 급상승 순위
            cursor.execute(f"""
                SELECT k.keyword_id, k.target_keyword, 
                       k.google_t_score_{period} AS score, 
                       k.google_delta_{period} AS delta, 
                       COUNT(t.tweet_id) AS mention_count
                FROM keyword k
                LEFT JOIN x_tweet t ON k.keyword_id = t.keyword_id 
                                   AND t.created_at >= DATE_SUB(NOW(), INTERVAL {period} DAY)
                WHERE k.google_delta_{period} IS NOT NULL
                GROUP BY k.keyword_id
                ORDER BY delta DESC LIMIT 10;
            """)
            google_surge = cursor.fetchall()

            # 실시간 트렌드 - 구글 언급량 순위
            cursor.execute(f"""
                SELECT k.keyword_id, k.target_keyword, 
                       k.google_t_score_{period} AS score, 
                       k.google_delta_{period} AS delta,
                       COUNT(t.tweet_id) AS mention_count
                FROM keyword k
                LEFT JOIN x_tweet t ON k.keyword_id = t.keyword_id 
                                   AND t.created_at >= DATE_SUB(NOW(), INTERVAL {period} DAY)
                WHERE k.google_t_score_{period} IS NOT NULL
                GROUP BY k.keyword_id
                ORDER BY mention_count DESC LIMIT 10;
            """)
            google_mention = cursor.fetchall()

        return {
            "status": "success",
            "data": {
                "integrated_surge": integrated_surge,
                "integrated_mention": integrated_mention,
                "naver_surge": naver_surge,
                "naver_mention": naver_mention,
                "google_surge": google_surge,
                "google_mention": google_mention
            }
        }

    except Exception as e:
        print(f"랭킹 조회 에러: {e}")
        raise HTTPException(status_code=500, detail="랭킹 데이터를 불러오는데 실패했습니다.")
    finally:
        conn.close()

# 키워드에 대한 최고 조회수 영상
@app.get("/get_recommended_video")
async def get_recommended_video(keyword: str, period: int=90):
    try:
        videos = await run_in_threadpool(search_recommend_videos, keyword, 1, period)

        if not videos:
            return {
                "status": "success",
                "message": "추천 영상을 찾지 못했습니다.",
                "count": 0,
                "data":[]
            }

        return {
            "status": "success",
            "count": len(videos),
            "data": videos
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추천 영상을 수집하는 중 오류 발생: {str(e)}")

# 키워드에 대한 최고 조회수 트윗
@app.get("/get_recommended_tweet")
async def get_recommended_tweet(keyword: str, period: int=90):
    try:
        tweets = await run_in_threadpool(search_trending_tweets,keyword, 1, period)

        if not tweets:
            return {
                "status": "success",
                "message": "추천 트윗을 찾지 못했습니다.",
                "count": 0,
                "data":[]
            }

        return {
            "status": "success",
            "count": len(tweets),
            "data": tweets
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추천 트윗을 수집하는 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("statistical_ranking_dispenser:app", host="0.0.0.0", port=8001, reload=True)