import datetime
import os

import pandas as pd
import pymysql
from googleapiclient.discovery import build
from youtubesearchpython import VideosSearch

# 테스트용 옵션
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

# API
API_KEY = 'AIzaSyDiyHQPSE7dSKPXDkY5MOhi0CseNv9RLR4'
youtube = build('youtube', 'v3', developerKey=API_KEY)

# 설정값
MAX_TRACK_DURATION = 7
MAX_VIDEOS = 100
MAX_COMMENTS = 10
MEASUREMENT_DURATION = 90

# 시간
now_time = datetime.datetime.now(datetime.timezone.utc)
measurement_time = now_time - datetime.timedelta(days=90)

# 블랙리스트 데이터 가져오기
def get_blacklist():
    videos_blacklist = set()
    comments_blacklist = set()

    try:
        conn = pymysql.connect(host='127.0.0.1', user='root', password='laplace1234', database='viral_finder', charset='utf8mb4')
        with conn.cursor() as cursor:
            cursor.execute('select type, identify_num from blacklist')
            for row in cursor.fetchall():
                if row[0] == 'video':
                    videos_blacklist.add(row[1])
                elif row[0] == 'comment':
                    comments_blacklist.add(row[1])
        conn.close()
    except Exception as e:
        print(f"블랙리스트를 가져오는데 실패했습니다 : {e}")

    return videos_blacklist, comments_blacklist

# 비디오
def search_videos(keyword, exclude_ids=None, max_result = 150):
    if exclude_ids is None:
        exclude_ids = set()

    video_ids = []
    videosSearch = VideosSearch(keyword, limit=50)
    next_page_token = None

    while len(video_ids) < max_result:
        results = videosSearch.result()

        if not results or not results.get('result'):
            break

        for video in results['result']:
            vid = video['id']
            if vid and vid not in exclude_ids and vid not in video_ids:
                video_ids.append(vid)

            if len(video_ids) >= max_result:
                break

        if len(video_ids) < max_result:
            if not videosSearch.next():
                break

    return video_ids

def video_stats(video_ids, batch_id, record_date, keyword):
    if not video_ids:
        print('해당 키워드가 포함된 영상을 찾을 수 없습니다!')
        return []

    videos_data = []

    for i in range(0, len(video_ids), 50):
        chunk_ids = video_ids[i:i + 50]

        video_response = youtube.videos().list(
            id=','.join(chunk_ids),
            part='snippet,statistics'
        ).execute()

        for item in video_response['items']:
            snippet = item['snippet']
            statistics = item.get('statistics',{})
            date_str = snippet.get('publishedAt', '')

            try:
                date = datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc)

                if date >= measurement_time:
                    videos_data.append({
                        '측정시간': record_date,
                        '그룹id': batch_id,
                        '영상id':item['id'],
                        '입력한 단어': keyword,
                        '조회수': int(statistics.get('viewCount', 0)),
                        '댓글수': int(statistics.get('commentCount', 0)),
                        '좋아요': int(statistics.get('likeCount', 0)),
                        '설명': snippet.get('description', ''),
                        '캡션명': snippet.get('title', ''),
                        '업로드 날짜': snippet.get('publishedAt', ''),
                    })

                    if len(videos_data) >= MAX_VIDEOS:
                        return videos_data

            except Exception as e:
                continue
    return videos_data

# 각 영상의 댓글
def Search_comment(video_id, batch_id, record_date, comments_blacklist=None, max_result = MAX_COMMENTS):
   if comments_blacklist is None:
       comments_blacklist = set()

   print(f"영상 ID {video_id}의 댓글 수집 중")
   comments_data = [];
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

           is_too_old = False

           for item in comments_response.get('items', []):
               comment = item['snippet']['topLevelComment']['snippet']
               comment_author = comment.get('authorDisplayName', '')
               published_at = comment.get('publishedAt', '')

               comment_date = datetime.datetime.strptime(published_at, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc)

               if comment_date < measurement_time:
                   is_too_old = True
                   break

               if comment_author in comments_blacklist:
                   continue

               comments_data.append({
                   '측정시간': record_date,
                   '그룹id': batch_id,
                   '영상id': video_id,
                   '댓글 번호': item['id'],
                   '캡션명': comment.get('authorDisplayName', ''),
                   '댓글 내용': comment.get('textDisplay', ''),
                   '좋아요': int(comment.get('likeCount', 0)),
                   '작성 날짜': published_at
               })

               if len(comments_data) >= max_result:
                   break

           if is_too_old or len(comments_data) >= MAX_COMMENTS:
               break

           next_page_token = comments_response.get('nextPageToken')
           if not next_page_token:
               break

       except Exception as e:
           print(f"댓글을 가져오는 중 에러 발생! 댓글을 달 수 없는 영상이거나 권한이 없습니다. : {e}")
           break

   return comments_data

# csv에 업데이트
def data_upload_to_csv(filename, data_list):
    if not data_list:
        return
    df = pd.DataFrame(data_list)

    file_exists = os.path.exists(filename)
    df.to_csv(filename, mode='a', header=not file_exists, index=False, encoding='utf-8-sig')

# 그룹(배치) 상태 확인
'''
    - 파일이 존재하지 않거나, 내용물이 비어있다면 번호를 처음부터 매김(DF_001)
    - 측정시간이 최대 측정 시간보다 낮으면 이전에 확인한 영상을 추적하고, 이전 그룹id에서 업데이트
    - 측정시간이 최대 측정 시간을 넘기면 새로운 영상 추적하고, 새로운 그룹id를 부여
'''
def check_batch_state(file_path):
    if not os.path.isfile(file_path):
        return True, "DF_001", []

    df = pd.read_csv(file_path)
    if df.empty:
        return True, "DF_001", []

    latest_batch = df['그룹id'].max()
    batch_df = df[df['그룹id'] == latest_batch]
    track_count = batch_df['측정시간'].nunique()

    if track_count < MAX_TRACK_DURATION:
        target_ids = batch_df['영상id'].unique().tolist()
        print(f"기존 영상 데이터({latest_batch})를 추적합니다. : {track_count}회 완료")
        return False, latest_batch, target_ids
    else:
        batch_num = int(latest_batch.split('_')[1])
        new_batch_id = f"DF_{batch_num + 1:03d}"
        print(f"{MAX_TRACK_DURATION}회 추적 완료! 새로운 영상 데이터를 탐색합니다.")
        return True, new_batch_id, []

def count_videos_today(keyword):
    today = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
    published_after = today.strftime('%Y-%m-%dT%H:%M:%SZ')

    try:
        response = youtube.search().list(
            q=keyword,
            part='id',
            type='video',
            publishedAfter=published_after,
            maxResults=1
        ).execute()

        total = response.get('pageInfo', {}).get('totalResults', 0)
        return total

    except Exception as e:
        print(f"측정 중 오류가 발생했습니다! : {e}")
        return 0

    return total


# main
def main():
    # python 테스트용(실제 사용 시 삭제)
    keyword = input("키워드를 입력하세요: ")

    # AWS 자동화용
    '''
        if len(sys.argv) > 1:
            keyword=sys.argv[1]
        else:
            keyword = DEFAULT_KEYWORD
    '''

    print("오늘 올라온 영상 갯수를 측정합니다...")
    today_count = count_videos_today(keyword)
    print(f"측정 완료! {keyword}에 대해 오늘 하루동안 올라온 영상은 {today_count}개 입니다.")

    print(f"'{keyword}' 데이터를 수집합니다...")

    # python 테스트용
    video_csv = f'videos_{keyword}.csv'
    comments_csv = f'comments_{keyword}.csv'

    # AWS 자동화용
    '''
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        video_csv = os.path.join(BASE_DIR, f'video_{keyword}.csv')
        comments_csv = os.path.join(BASE_DIR, f'comments_{keyword}.csv')
    '''

    record_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 블랙 리스트 확인
    videos_blacklist, comments_blacklist = get_blacklist()
    is_new_batch, batch_id, target_ids = check_batch_state(video_csv)

    if not is_new_batch:
        valid_targets = [vid for vid in target_ids if vid not in videos_blacklist]
        shortfall = MAX_VIDEOS - len(valid_targets)

        if shortfall > 0:
            print(f"'{keyword}'에 대한 데이터를 {shortfall}개 만큼 보충하기 위해 탐색합니다...")
            exclude_set = videos_blacklist.union(set(valid_targets))
            new_vids = search_videos(keyword, exclude_ids=exclude_set, max_result=shortfall)
            target_ids = valid_targets + new_vids

        else:
            target_ids = valid_targets

    else:
        print(f"'{keyword}'에 대한 새로운 영상을 탐색중입니다...")
        target_ids = search_videos(keyword, exclude_ids=videos_blacklist, max_result=MAX_VIDEOS)
        if not target_ids:
            print("오류 : 영상을 찾을 수 없습니다.")
            return

    print("영상 데이터를 수집 및 csv에 업데이트 하는 중...")
    videos_data = video_stats(target_ids, batch_id, record_date, keyword)
    videos_data = sorted(videos_data, key=lambda x: x['업로드 날짜'], reverse=True)
    data_upload_to_csv(video_csv, videos_data)

    print("댓글 데이터를 수집 및 csv에 업데이트 하는 중...")
    comments_data = []
    final_target_ids = [video['영상id'] for video in videos_data]
    for video_id in final_target_ids:
        single_video_comments = Search_comment(video_id, batch_id, record_date, comments_blacklist=comments_blacklist, max_result=MAX_COMMENTS)
        single_video_comments = sorted(single_video_comments, key=lambda x : x['작성 날짜'], reverse=True)
        comments_data.extend(single_video_comments)
    data_upload_to_csv(comments_csv, comments_data)

    print(f"작업 완료! [{record_date}] 데이터 저장 성공\n")

if __name__ == "__main__":
    main()