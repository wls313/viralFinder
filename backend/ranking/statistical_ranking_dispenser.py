import pymysql, os, sys

from fastapi import FastAPI, HTTPException
from progress_state import progress
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.concurrency import run_in_threadpool

current_dir = os.path.dirname(os.path.realpath(__file__))
top_level_dir = os.path.dirname(current_dir)
if top_level_dir not in sys.path:
    sys.path.append(top_level_dir)

from key_setting import host_ip, user_value, password_value, database_name
from crawling.x_data_abstraction import search_trending_tweets
from crawling.new_youtube_data_abstraction import search_recommend_videos

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

def get_db_connection():
    return pymysql.connect(host=host_ip, user=user_value, password=password_value, database=database_name,
                           charset='utf8mb4')

# 언급량 통계
@app.get("/get_mention_volume_ranking")
def get_mention_volume_ranking():
    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            sql_query = """
                    select k.keyword_id, k.target_keyword, count(x.keyword_id) as mention_count from keyword k
                    join x_tweet x on x.keyword_id = k.keyword_id where x.created_at >= DATE_SUB(NOW(), INTERVAL 1 MONTH)
                    group by k.keyword_id, k.target_keyword order by mention_count desc limit 30; 
                """
            cursor.execute(sql_query)
            results = cursor.fetchall()

            return {
                "status": "success",
                "message": "언급량 랭킹을 성공적으로 불러왔습니다.",
                "count": len(results),
                "data": results
            }

    except Exception as e:
        print(f"언급량 랭킹을 불러오는데 실패했습니다: {e}")
        raise HTTPException(status_code=500, detail=f"언급량 랭킹 데이터를 가져오는 중 오류 발생: {str(e)}")
    finally:
        conn.close()

# 조회수 통계
@app.get("/get_search_volume_ranking")
def get_search_volume_ranking():
    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 중요: 현재 네이버/구글의 한 달간 상대적 검색량의 합계를 보내는데 이에 대해 피드백이 필요
            sql_query = """
                    select k.keyword_id, k.target_keyword, SUM(search_data.relative_ratio) as total_relative_ratio from keyword k
                    join (select keyword_id, relative_ratio from google where period >= DATE_SUB(NOW(), INTERVAL 1 MONTH)
                    union all
                    select keyword_id, relative_ratio from naver where period >= DATE_SUB(NOW(), INTERVAL 1 MONTH)) 
                    as search_data on k.keyword_id = search_data.keyword_id
                    group by k.keyword_id, k.target_keyword order by total_relative_ratio desc limit 30;
                """
            cursor.execute(sql_query)
            results = cursor.fetchall()

            return {
                "status": "success",
                "message": "검색량 랭킹을 성공적으로 불러왔습니다.",
                "count": len(results),
                "data": results
            }

    except Exception as e:
        print(f"조회수 랭킹을 불러오는데 실패했습니다: {e}")
        raise HTTPException(status_code=500, detail=f"조회수 랭킹 데이터를 가져오는 중 오류 발생: {str(e)}")
    finally:
        conn.close()

# 추천 영상
@app.get("/get_recommended_video")
async def get_recommended_video():
    try:
        videos = await run_in_threadpool(search_recommend_videos)

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

# 추천 트윗
@app.get("/get_recommended_tweet")
async def get_recommended_tweet():
    try:
        tweets = await run_in_threadpool(search_trending_tweets)

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