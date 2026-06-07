import datetime
import os
import time
from googleapiclient.discovery import build
import pandas as pd
import pymysql

from key_setting import youtube_api_key, host_ip, user_value, password_value, database_name
import words_extractor
import xgboost_interpretation

# 테스트용 옵션
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

# API
youtube = build('youtube', 'v3', developerKey=youtube_api_key)

# 설정값
MAX_VIDEOS = 300
MAX_COMMENTS = 100
YESTERDAY = 1

# 시간
now_time = datetime.datetime.now(datetime.timezone.utc)
measurement_time = (now_time - datetime.timedelta(days=YESTERDAY))
measurement_time_iso = measurement_time.strftime('%Y-%m-%dT%H:%M:%SZ')

# 블랙리스트 데이터 가져오기
def get_blacklist():
    videos_blacklist = set()
    comments_blacklist = set()

    try:
        with pymysql.connect(host=host_ip, user=user_value, password=password_value, database=database_name, charset='utf8mb4') as conn:
            with conn.cursor() as cursor:
                cursor.execute('select type, identify_num from blacklist')
                for row in cursor.fetchall():
                    if row[0] == 'video':
                        videos_blacklist.add(row[1])
                    elif row[0] == 'comment':
                        comments_blacklist.add(row[1])
    except Exception as e:
        print(f"오류-블랙리스트를 가져오는데 실패했습니다 : {e}")

    return videos_blacklist, comments_blacklist

# 오늘 올라온 영상 갯수
def count_videos(keyword):
    print("오늘 업로드된 총 영상 수를 집계합니다...")

    try:
        response = youtube.search().list(
            q=keyword,
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

# 댓글 수
def comment_count(video_ids):
    print("오늘 작성된 총 댓글 수를 집계합니다...")
    comments_count_dict = {}

    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i + 50]
        try:
            response = youtube.videos().list(
                id=','.join(chunk),
                part='statistics',
            ).execute()

            for item in response.get('items', []):
                video_id = item['id']
                total_comments = int(item.get('statistics', {}).get('commentCount', 0))
                comment_count_dict[video_id] = total_comments

        except Exception as e:
            print(f"오류-댓글 집계 중 오류가 발생했습니다! : {e}")

    return comment_count_dict

# 영상 탐색
def search_videos(keyword, exclude_ids=None, max_result = 150):
    print(f"오늘 업로드 된 {keyword}와 관련된 영상을 탐색합니다...")

    video_ids = []
    file_dir = os.path.dirname(os.path.abspath(__file__))
    tracking_file = os.path.join(file_dir, f'youtube_{keyword}.csv')

    if os.path.exists(tracking_file):
        df = pd.read_csv(tracking_file)
        if '영상id' in df.columns:
            video_ids = df['영상id'].dropna().tolist()
            print(f"기존에 추적 중인 영상 {len(video_ids)}개를 불러옵니다...")

    new_video_ids = []
    next_page_token = None

    while len(video_ids) + len(new_video_ids) < max_result:
        try:
            request = youtube.search().list(
                part="id",
                q=keyword,
                type="video",
                publishedAfter=measurement_time_iso,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()

            for item in response.get('items', []):
                video = item['id'].get('videoId')
                if video and video not in exclude_ids and video not in video_ids and video not in new_video_ids:
                    new_video_ids.append(video)

            next_page_token = response.get('nextPageToken')

            if not next_page_token:
                break

        except Exception as e:
            print(f"오류-유튜브 API에 검색 중 에러가 발생했습니다 : {e}")
            break

    print(f"총 {len(video_ids)}개의 영상을 찾았습니다...")

    final_videos = (video_ids + new_video_ids)[:MAX_VIDEOS]

    # 다음을 위해 추적 파일 업데이트
    pd.DataFrame({'영상id': final_videos}).to_csv(tracking_file, index=False, encoding='utf-8-sig')
    print(f'총 {len(final_videos)}개의 영상을 확정했습니다!')

    return final_videos


def video_stats(video_ids, record_date):
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
                    '측정기간' : record_date,
                    '영상id' : video_id,
                    '일일 조회수': int(stats.get('viewCount', 0)),
                    '일일 좋아요수': int(stats.get('likeCount', 0)),
                    '일일 총댓글수': int(stats.get('commentCount', 0))
                })
        except Exception as e:
            print(f"오류-영상 데이터를 저장하는 도중 에러가 발생했습니다 : {e}")

    return videos_data_list

# 각 영상의 댓글
def search_comment(video_id, record_date, keyword, comments_blacklist=None, max_result = MAX_COMMENTS):
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
                   '측정기간': record_date,
                   '영상id': video_id,
                   '댓글 번호': item['id'],
                   '캡션명': comment.get('authorDisplayName', '').strip(),
                   '댓글 내용': comment.get('textDisplay', ''),
                   '좋아요': int(comment.get('likeCount', 0)),
                   '작성 날짜': published_at,
                   '광고여부': 0
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

   comments_text_list = [c['댓글 내용'] for c in comments_data]
   print(f"댓글{len(comments_text_list)}개 판독 시작...")

   batch_results = words_extractor.AD_search(comments_text_list, keyword)
   time.sleep(4)

   for i in range(len(comments_data)):
       if comments_data[i]['캡션명'] in comments_blacklist:
           comments_data[i]['광고여부'] = 1
       else:
           comments_data[i]['광고여부'] = batch_results[i]

   return comments_data

# csv에 업데이트
def data_upload_to_csv(filename, data_list):
    if not data_list:
        return
    df = pd.DataFrame(data_list)
    file_exists = os.path.exists(filename)
    last_updated = 0

    if file_exists:
        try:
            df_before = pd.read_csv(filename)
            if '업데이트 횟수' in df_before.columns:
                last_updated = df_before['업데이트 횟수'].max()
        except pd.errors.EmptyDataError:
            pass

    current_update = last_updated + 1
    df.insert(0, '업데이트 횟수', current_update)

    df.to_csv(filename, mode='a', header=not file_exists, index=False, encoding='utf-8-sig')
    return current_update

# main
def main():
    keyword = input("키워드를 입력하세요: ")
    record_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    video_csv = f'videos_{keyword}.csv'
    comments_csv = f'comments_{keyword}.csv'

    today_video_count = count_videos(keyword)
    print(f"측정 완료! {keyword}에 대해 오늘 하루동안 올라온 영상은 {today_video_count}개 입니다.")
    print(f"'{keyword}' 데이터를 수집합니다...")

    # 블랙 리스트 확인
    videos_blacklist, comments_blacklist = get_blacklist()
    target_ids = search_videos(keyword, exclude_ids=videos_blacklist, max_result=MAX_VIDEOS)

    if not target_ids:
        print("수집할 영상이 없어 종료됩니다.")
        return 0

    print("영상 데이터를 수집 및 csv에 업데이트 하는 중...")
    videos_data = video_stats(target_ids, record_date)
    current_updated = data_upload_to_csv(video_csv, videos_data)

    # 댓글 데이터 수집
    comments_data = []

    for idx, video_id in enumerate(target_ids):
        if idx > 0 and idx % 50 == 0:
            print(f"영상 {idx}개 처리 완료!")
        single_video_comments = search_comment(
            video_id = video_id,
            record_date = record_date,
            keyword = keyword,
            comments_blacklist = comments_blacklist,
            max_result = MAX_COMMENTS
        )
        comments_data.extend(single_video_comments)

    print("댓글 데이터를 수집 및 csv에 업데이트 하는 중...")
    data_upload_to_csv(comments_csv, comments_data)

    print(f"작업 완료! [{record_date}] 데이터 저장 성공\n")

    if current_updated >= 7:
        print(f"해당 키워드의 데이터가 {current_updated}번 업데이트 되었습니다. 충분한 데이터를 얻었기에 바이럴 판독을 시작합니다.")
        xgboost_interpretation.viral_interpretation(keyword)

if __name__ == "__main__":
    main()