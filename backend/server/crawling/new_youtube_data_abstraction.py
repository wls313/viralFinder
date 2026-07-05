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
    sys.path.append(top_level_dir)

from key_setting import youtube_api_key, host_ip, user_value, password_value, database_name
from analyzer import words_extractor, random_forest_interpretation

# 테스트용 옵션
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

# API
youtube = build('youtube', 'v3', developerKey=youtube_api_key)

# 설정값
MAX_VIDEOS = 100
MAX_COMMENTS = 100
WEAK = 7
DEFAULT_KEYWORD = "단소살인마"

# 시간
now_time = datetime.datetime.now(datetime.timezone.utc)
measurement_time = (now_time - datetime.timedelta(days=WEAK))
measurement_time_iso = measurement_time.strftime('%Y-%m-%dT%H:%M:%SZ')

def get_db_connection():
    return pymysql.connect(host=host_ip, user=user_value, password=password_value, database=database_name,
                           charset='utf8mb4')

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


# 블랙리스트 데이터 가져오기
def get_blacklist():
    comments_blacklist = set()
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('select caption_name from blacklist')
            for row in cursor.fetchall():
                comments_blacklist.add(row[0])
    except Exception as e:
        print(f"오류-블랙리스트를 가져오는데 실패했습니다 : {e}")
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()

    return comments_blacklist

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
def search_videos(keyword, keyword_id, exclude_ids=None, max_result = 150):
    print(f"오늘 업로드 된 {keyword}와 관련된 영상을 탐색합니다...")

    if exclude_ids is None:
        exclude_ids = set()

    video_ids = []
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT video_id FROM youtube WHERE keyword_id=%s", (keyword_id,))
            existing_ids = [row[0] for row in cursor.fetchall()]
            video_ids.extend(existing_ids)
            print(f"기존에 추적 중인 영상 {len(video_ids)}개를 불러옵니다...")
    except Exception as e:
        print(f"DB 조회 오류: {e}")
    finally:
        conn.close()

    new_video_ids = []
    next_page_token = None

    keyword_clean = keyword.replace(' ', '').lower()

    while len(video_ids) + len(new_video_ids) < max_result:
        try:
            request = youtube.search().list(
                part="id,snippet",
                q=f'"{keyword}"',
                type="video",
                publishedAfter=measurement_time_iso,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()

            for item in response.get('items', []):
                video = item['id'].get('videoId')

                if not video or video in exclude_ids or video in video_ids or video in new_video_ids:
                    continue

                snippet = item.get('snippet')
                title_clean = snippet.get('title', '').replace(" ", "").lower()
                description_clean = snippet.get('description', '').replace(" ", "").lower()

                if keyword_clean in title_clean or keyword_clean in description_clean:
                    new_video_ids.append(video)

            next_page_token = response.get('nextPageToken')

            if not next_page_token:
                break

        except Exception as e:
            print(f"오류-유튜브 API에 검색 중 에러가 발생했습니다 : {e}")
            break

    print(f"총 {len(video_ids)}개의 영상을 찾았습니다...")

    final_videos = (video_ids + new_video_ids)[:MAX_VIDEOS]
    print(f'총 {len(final_videos)}개의 영상을 확정했습니다!')

    return final_videos


def video_stats(video_ids, record_date, keyword_id):
    print("수집된 영상의 조회수/좋아요 수 수집하는 중...")
    videos_data_list = []

    for i in range(0, len(video_ids), 50):
        chunk_ids = video_ids[i:i + 50]
        try:
            video_response = youtube.videos().list(
                id=','.join(chunk_ids),
                part='statistics',
            ).execute()

            for item in video_response.get('items', []):
                video_id = item['id']
                stats = item.get('statistics', {})
                videos_data_list.append({
                    'record_date' : record_date,
                    'video_id' : video_id,
                    'keyword_id' : keyword_id,
                    'daily_view_count': int(stats.get('viewCount', 0)),
                    'daily_like_count': int(stats.get('likeCount', 0)),
                    'daily_comment_count': int(stats.get('commentCount', 0))
                })
        except Exception as e:
            print(f"오류-영상 데이터를 저장하는 도중 에러가 발생했습니다 : {e}")

    return videos_data_list

# 각 영상의 댓글
def search_comment(video_id, record_date, keyword, keyword_id, comments_blacklist=None, max_result = MAX_COMMENTS):
   if comments_blacklist is None:
       comments_blacklist = set()

   print(f"영상 ID {video_id}의 댓글 수집 중")
   comments_data = []
   next_page_token = None

   while len(comments_data) < max_result:
       try:
           comments_response = youtube.commentThreads().list(
               videoId = video_id,
               part = 'snippet',
               maxResults = 50,
               textFormat = 'plainText',
               pageToken = next_page_token,
               order='time'
           ).execute()

           items = comments_response.get('items', [])
           if not items:
               break

           for item in items:
               comment = item['snippet']['topLevelComment']['snippet']
               published_at = comment.get('publishedAt', '')

               comment_date = datetime.datetime.strptime(published_at, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc)

               if comment_date < measurement_time:
                   break

               comments_data.append({
                   'video_id': video_id,
                   'record_date': record_date,
                   'keyword_id': keyword_id,
                   'caption_name': comment.get('authorDisplayName', '').strip(),
                   'content': comment.get('textDisplay', ''),
                   'like_count': int(comment.get('likeCount', 0)),
                   'is_ad': 0
               })

               if len(comments_data) >= max_result:
                   break

           next_page_token = comments_response.get('nextPageToken')
           if not next_page_token:
               break

       except Exception as e:
           print(f"오류-댓글을 가져오는 중 에러 발생! 댓글을 달 수 없는 영상이거나 권한이 없습니다. : {e}")
           break

   if not comments_data:
       return []

   comments_text_list = [c['content'] for c in comments_data]
   print(f"댓글{len(comments_text_list)}개 판독 시작...")

   batch_results = words_extractor.AD_search(comments_text_list, keyword)
   time.sleep(4)

   for i in range(len(comments_data)):
       caption = comments_data[i]['caption_name']
       is_blacklist = False

       for black_user in comments_blacklist:
           if black_user in caption:
               is_blacklist = True
               break

       if is_blacklist:
           comments_data[i]['is_ad'] = 1
           print(f"{caption}을 블랙리스트에 저장했습니다...")
       else:
           comments_data[i]['is_ad'] = batch_results[i]

   return comments_data

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

# comment 데이터를 db에 업데이트
def comment_upload_to_db(data_list, update_count, keyword_id):
    if not data_list:
        return

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            for data in data_list:
                data['update_count'] = update_count;
                data['keyword_id'] = keyword_id

            keys = ",".join(data_list[0].keys())
            vals = ",".join(["%s"] * len(data_list[0]))
            sql = f"INSERT INTO youtube_comments ({keys}) VALUES ({vals})"
            cursor.executemany(sql, [tuple(data.values()) for data in data_list])
        conn.commit()
    except Exception as e:
        print(f"오류-댓글을 DB에 저장하는 중 에러가 발생했습니다 : {e}")
    finally:
        conn.close()

# main
def run_search(keyword):
    record_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    today_video_count = count_videos(keyword)
    print(f"측정 완료! {keyword}에 대해 오늘 하루동안 올라온 영상은 {today_video_count}개 입니다.")

    keyword_id = get_keyword_id(keyword)
    print(f"'{keyword}(keyword_id: {keyword_id})' 데이터를 수집합니다...")

    # 블랙 리스트 확인
    comments_blacklist = get_blacklist()
    target_ids = search_videos(keyword, keyword_id, exclude_ids=None, max_result=MAX_VIDEOS)

    if not target_ids:
        print("수집할 영상이 없어 종료됩니다.")
        return {"status": "ERROR", "message": "수집할 영상이 없습니다."}

    print("영상 데이터를 수집 및 csv에 업데이트 하는 중...")
    videos_data = video_stats(target_ids, record_date, keyword_id)
    current_updated = video_upload_to_db(videos_data, keyword_id)

    # 댓글 데이터 수집
    comments_data = []

    for idx, video_id in enumerate(target_ids):
        if idx > 0 and idx % 50 == 0:
            print(f"영상 {idx}개 처리 완료!")
        single_video_comments = search_comment(
            video_id = video_id,
            record_date = record_date,
            keyword = keyword,
            keyword_id = keyword_id,
            comments_blacklist = comments_blacklist,
            max_result = MAX_COMMENTS
        )
        comments_data.extend(single_video_comments)

    print("댓글 데이터를 수집 및 csv에 업데이트 하는 중...")
    comment_upload_to_db(comments_data, current_updated, keyword_id)

    result_json = {
        "status": "success",
        "keyword": keyword,
        "update_count": current_updated,
        "analysis": None
    }

    print(f"작업 완료! [{record_date}] 데이터 저장 성공\n")

    if current_updated >= 7:
        print(f"해당 키워드의 데이터가 {current_updated}번 업데이트 되었습니다. 충분한 데이터를 얻었기에 바이럴 판독을 시작합니다.")
        #xgboost_interpretation.viral_interpretation(keyword)
        results = random_forest_interpretation.viral_interpretation(keyword)
        result_json['analysis'] = results
    else:
        result_json['analysis'] = f"데이터 수집(업데이트 횟수: {current_updated})"

    print(json.dumps(result_json, ensure_ascii=False, indent=4))
    return result_json

if __name__ == "__main__":
    run_search(DEFAULT_KEYWORD)