import datetime
import os, sys
import time
import json
from googleapiclient.discovery import build
import pandas as pd
import pymysql

# 상위(server) 폴더 경로
current_dir = os.path.dirname(os.path.realpath(__file__))
top_level_dir = os.path.dirname(current_dir)
if top_level_dir not in sys.path:
    sys.path.insert(0, top_level_dir)

from config.config import youtube_api_key, DB_CONFIG

# 그래프(TrendChart)용 네이버/구글 트렌드 데이터 수집
from crawling.naver_data_lab_crawling import search_keyword as crawl_naver_trend
from crawling.pytrends_crawling import search_keyword as crawl_google_trend
from crawling.apify_x_crawling import search_x as crawl_x_trend
from config.database import fetch_data

# 테스트용 옵션
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

# API
youtube = build('youtube', 'v3', developerKey=youtube_api_key)

# 설정값
MAX_VIDEOS = 150
WEAK = 7
DEFAULT_KEYWORD = "여아"
SEARCHING_RECOMMEND_VIDEO_COUNTS = 10
# 네이버/구글 트렌드 조회 기간(일). /search가 아직 프론트의 period 프리셋을
# 안 받고 있어서 우선 고정값 사용.
TREND_SEARCH_RANGE_DEFAULT = 7

# 시간
now_time = datetime.datetime.now(datetime.timezone.utc)
measurement_time = (now_time - datetime.timedelta(days=WEAK))
measurement_time_iso = measurement_time.strftime('%Y-%m-%dT%H:%M:%SZ')

def get_db_connection():
    return pymysql.connect(host=DB_CONFIG["host"], user=DB_CONFIG["user"], password=DB_CONFIG["password"], database=DB_CONFIG["database"],
                           charset=DB_CONFIG["charset"])

# 키워드 ID 조회 및 Insert
def get_keyword_id(keyword):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT keyword_id FROM keyword WHERE target_keyword=%s", (keyword,))
            keyword_result = cursor.fetchone()
            if keyword_result:
                return keyword_result[0]

            cursor.execute("INSERT INTO keyword (target_keyword) VALUES (%s)", (keyword,))
            conn.commit()
            return cursor.lastrowid
    finally:
        conn.close()


# 오늘 올라온 영상 갯수
def count_videos(keyword):
    print("오늘 업로드된 총 영상 수를 집계합니다...")

    try:
        response = youtube.search().list(
            q=f'"{keyword}"',
            part='id',
            type='video',
            publishedAfter=measurement_time_iso,
            maxResults=1
        ).execute()

        total = response.get('pageInfo', {}).get('totalResults', 0)
        return total

    except Exception as e:
        print(f"오류-영상 집계 중 오류가 발생했습니다! : {e}")
        return 0

    return total

# 영상 탐색
def search_videos(keyword, keyword_id, exclude_ids=None):
    print(f"오늘 업로드 된 {keyword}와 관련된 영상을 탐색합니다...")

    set_exclude_ids = set(exclude_ids) if exclude_ids else set()
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT video_id FROM youtube WHERE keyword_id=%s", (keyword_id,))
            existing_ids = [row[0] for row in cursor.fetchall()]
            set_exclude_ids.update(existing_ids)
            print(f"기존에 추적 중인 영상 {len(existing_ids)}개를 불러옵니다...")
    except Exception as e:
        print(f"DB 조회 오류: {e}")
    finally:
        conn.close()

    new_video_ids = []
    next_page_token = None

    keyword_clean = keyword.replace(' ', '').lower()

    while len(existing_ids) + len(new_video_ids) < MAX_VIDEOS:
        try:
            request = youtube.search().list(
                part="id,snippet",
                q=f'"{keyword}"',
                type="video",
                publishedAfter=measurement_time_iso,
                maxResults=min(MAX_VIDEOS, 50),
                pageToken=next_page_token
            )
            response = request.execute()

            for item in response.get('items', []):
                video = item['id'].get('videoId')
                if not video or video in set_exclude_ids or video in new_video_ids:
                    continue

                snippet = item.get('snippet', {})
                keyword_check = (snippet.get('title', '') + snippet.get('description', '')).replace(' ', '').lower()

                if keyword_clean in keyword_check:
                    new_video_ids.append(video)
                    if len(new_video_ids) + len(set_exclude_ids) >= MAX_VIDEOS:
                        break

            next_page_token = response.get('nextPageToken')

            if not next_page_token:
                break

        except Exception as e:
            print(f"오류-유튜브 API에 검색 중 에러가 발생했습니다 : {e}")
            break

    final_videos = list(new_video_ids) + list(set_exclude_ids)
    print(f'총 {len(final_videos)}개의 영상을 확정했습니다!')

    return final_videos[:MAX_VIDEOS]


def video_stats(video_ids, record_date, keyword_id):
    print("수집된 영상의 데이터를 수집하는 중...")
    videos_data_list = []

    for i in range(0, len(video_ids), 50):
        chunk_ids = video_ids[i:i + 50]
        try:
            video_response = youtube.videos().list(
                id=','.join(chunk_ids),
                part='snippet, statistics'
            ).execute()

            searching_ids = set()
            for item in video_response.get('items', []):
                video_id = item['id']
                searching_ids.add(video_id)
                stats = item.get('statistics', {})
                snippet = item.get('snippet', {})
                videos_data_list.append({
                    'record_date' : record_date,
                    'video_id' : video_id,
                    'keyword_id' : keyword_id,
                    'title' : snippet.get('title', ''),
                    'daily_view_count': int(stats.get('viewCount', 0)),
                    'daily_like_count': int(stats.get('likeCount', 0)),
                    'daily_comment_count': int(stats.get('commentCount', 0)),
                    'url': f'https://www.youtube.com/watch?v={video_id}'
                })

            if len(searching_ids) < len(chunk_ids):
                print(f"삭제나 비공개 등에 의해 {len(chunk_ids) - len(searching_ids)}개의 영상의 정보를 가져올 수 없었습니다.")

        except Exception as e:
            print(f"오류-영상 데이터를 저장하는 도중 에러가 발생했습니다 : {e}")

    return videos_data_list

# video 데이터를 db에 업데이트
def video_upload_to_db(data_list, keyword_id):
    if not data_list:
        return 0

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
           cursor.execute("SELECT MAX(update_count) FROM youtube WHERE keyword_id=%s", (keyword_id,))
           results = cursor.fetchone()[0]
           current_update = (results if results else 0) + 1

           for data in data_list:
               data['update_count'] = current_update

           keys = ",".join(data_list[0].keys())
           vals = ",".join(["%s"] * len(data_list[0]))
           sql = f"INSERT INTO youtube ({keys}) VALUES ({vals})"
           cursor.executemany(sql, [tuple(data.values()) for data in data_list])
        conn.commit()
        return current_update
    except Exception as e:
        print(f"오류-영상을 DB에 저장하는 중 에러가 발생했습니다 : {e}")
        return 0
    finally:
        conn.close()


# 네이버/구글 트렌드를 수집하고, 프론트 TrendChart가 기대하는
# [{period, ratio}, ...] 형태로 가공해서 반환
def get_trend_chart_data(keyword, search_range=TREND_SEARCH_RANGE_DEFAULT):
    try:
        crawl_naver_trend(keyword, search_range)
    except Exception as e:
        print(f"오류-네이버 트렌드 수집 실패 (그래프 데이터 일부 누락될 수 있음): {e}")

    try:
        crawl_google_trend(keyword, search_range)
    except Exception as e:
        print(f"오류-구글 트렌드 수집 실패 (그래프 데이터 일부 누락될 수 있음): {e}")

    try:
        crawl_x_trend(keyword, search_range)
    except Exception as e:
        print(f"오류-X 트윗 수집 실패 (그래프 데이터 일부 누락될 수 있음): {e}")

    try:
        trend_df, _video_df, keyword_id = fetch_data(keyword)
    except Exception as e:
        print(f"오류-트렌드 데이터 조회 실패: {e}")
        return [], [], []

    naver_trend = []
    google_trend = []

    if trend_df is not None and not trend_df.empty:
        naver_trend = [
            {"period": row["period"].strftime("%Y-%m-%d"), "ratio": float(row["weight_naver"])}
            for _, row in trend_df.iterrows()
        ]
        google_trend = [
            {"period": row["period"].strftime("%Y-%m-%d"), "ratio": float(row["weight_google"])}
            for _, row in trend_df.iterrows()
        ]

    x_trend = []
    try:
        if keyword_id:
            conn = get_db_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT DATE(created_at) AS period, COUNT(*) AS tweet_count
                        FROM x_tweet
                        WHERE keyword_id = %s
                          AND created_at >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                        GROUP BY DATE(created_at)
                        ORDER BY period
                        """,
                        (keyword_id, search_range),
                    )
                    rows = cursor.fetchall()
                    x_trend = [
                        {"period": row[0].strftime("%Y-%m-%d"), "ratio": int(row[1])}
                        for row in rows
                    ]
            finally:
                conn.close()
    except Exception as e:
        print(f"오류-X 트렌드 집계 실패 (그래프 데이터 일부 누락될 수 있음): {e}")

    return naver_trend, google_trend, x_trend

# main
def run_search(keyword):
    record_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    today_video_count = count_videos(keyword)
    print(f"측정 완료! {keyword}에 대해 오늘 하루동안 올라온 영상은 {today_video_count}개 입니다.")

    keyword_id = get_keyword_id(keyword)
    print(f"'{keyword}(keyword_id: {keyword_id})' 데이터를 수집합니다...")

    # 블랙 리스트 확인
    target_ids = search_videos(keyword, keyword_id, exclude_ids=None)

    if not target_ids:
        print("수집할 영상이 없어 종료됩니다.")
        return {"status": "ERROR", "message": "수집할 영상이 없습니다."}

    print("영상 데이터를 수집 및 csv에 업데이트 하는 중...")
    videos_data = video_stats(target_ids, record_date, keyword_id)
    current_updated = video_upload_to_db(videos_data, keyword_id)

    print("네이버/구글/X 트렌드 데이터를 수집하는 중...")
    naver_trend, google_trend, x_trend = get_trend_chart_data(keyword)

    result_json = {
        "status": "success",
        "keyword": keyword,
        "update_count": current_updated,
        "analysis": None,
        "naver_trend": naver_trend,
        "google_trend": google_trend,
        "x_trend": x_trend
    }

    print(f"작업 완료! [{record_date}] 데이터 저장 성공\n")

    return result_json


def search_recommend_videos(video_count=SEARCHING_RECOMMEND_VIDEO_COUNTS):
    try:
        request = youtube.videos().list(
            part='snippet',
            chart="mostPopular",
            regionCode="KR",
            maxResults=video_count
        )
        response = request.execute()
    except Exception as e:
        print(f"추천 영상을 탐색하던 중 에러 발생: {e}")
        return []

    items = response.get('items', [])
    if not items:
        print("수집된 추천 영상이 없습니다.")
        return []

    results = []
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            sql_query = """
                insert into recommend (type, url, content, published_date) values (%s, %s, %s, %s)
                    on duplicate key update content = VALUES(content)
            """

            for item in items:
                video_id = item.get('id')
                snippet = item.get('snippet', {})

                video_url = f"https://www.youtube.com/watch?v={video_id}"
                title = snippet.get('title', '')

                raw_time = snippet.get('publishedAt')
                if raw_time:
                    try:
                        created_at = datetime.datetime.fromisoformat(raw_time.replace('Z', '+00:00'))
                        created_at_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
                    except Exception as e:
                        created_at_str = None
                else:
                    created_at_str = None

                values = (
                    "youtube",
                    video_url,
                    title,
                    created_at_str
                )
                cursor.execute(sql_query, values)

                results.append({
                    "type": "youtube",
                    "url": video_url,
                    "full_text": title,
                    "created_at": created_at_str
                })
            conn.commit()
            print(f"추천 영상을 DB에 저장했습니다")

    except Exception as e:
        print(f"API로 추천 영상을 서칭하는 중 오류가 발생했습니다: {e}")
        conn.rollback()
    finally:
        conn.close()

    return results


if __name__ == "__main__":
    run_search(DEFAULT_KEYWORD)