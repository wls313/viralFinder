import datetime
import os
import sys
from googleapiclient.discovery import build
import pandas as pd

# 테스트용 옵션
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

# API
API_KEY = 'AIzaSyCx-AlOUq3HNhSQkF0y33RX-5uDQcerEvM'
youtube = build('youtube', 'v3', developerKey=API_KEY)

# 설정값
MAX_TRACK_DURATION = 7
MAX_VIDEOS = 5
MAX_COMMENTS = 5
DEFAULT_KEYWORD = "Never Gonna Give You Up" # 디폴트 값

# 비디오
def search_videos(keyword, max_result = MAX_VIDEOS):
    kor_now = datetime.datetime.now().astimezone()
    today_start_local = kor_now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_start_utc = today_start_local.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    search_response = youtube.search().list(
        q = keyword,
        type = 'video',
        part = 'id',
        maxResults = max_result,
        order = 'date'
    ).execute()

    video_ids = [item['id']['videoId'] for item in search_response['items'] if item['id'].get('videoId')]

    return video_ids

def video_stats(video_ids, batch_id, record_date, keyword):
    if not video_ids:
        print('해당 키워드가 포함된 영상을 찾을 수 없습니다!')
        return []

    video_response = youtube.videos().list(
        id = ','.join(video_ids),
        part = 'snippet,statistics'
    ).execute()

    videos_data = []

    for item in video_response['items']:
        snippet = item['snippet']
        statistics = item.get('statistics',{})

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

    return videos_data

# 각 영상의 댓글
def Search_comment(video_id, batch_id, record_date, max_result = MAX_COMMENTS):
   print(f"영상 ID {video_id}의 댓글 수집 중")
   comments_data = [];

   try:
       comments_response = youtube.commentThreads().list(
           videoId = video_id,
           part = 'snippet',
           maxResults = max_result,
           textFormat = 'plainText'
       ).execute()

       for item in comments_response.get('items', []):
           comment = item['snippet']['topLevelComment']['snippet']
           comments_data.append({
               '측정시간': record_date,
               '그룹id': batch_id,
               '영상id': video_id,
               '댓글 번호': item['id'],
               '캡션명': comment.get('authorDisplayName', ''),
               '댓글 내용': comment.get('textDisplay', ''),
               '좋아요': int(comment.get('likeCount', 0))
           })

   except Exception as e:
       print(f"댓글을 가져오는 중 에러 발생 : {e}")

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

    print(f"'{keyword}' 데이터를 수집합니다...")

    # python 테스트용
    video_csv = f'video_{keyword}.csv'
    comments_csv = f'comments_{keyword}.csv'

    # AWS 자동화용
    '''
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        video_csv = os.path.join(BASE_DIR, f'video_{keyword}.csv')
        comments_csv = os.path.join(BASE_DIR, f'comments_{keyword}.csv')
    '''

    record_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    is_new_batch, batch_id, target_ids = check_batch_state(video_csv)

    if is_new_batch:
        print(f"'{keyword}'에 대한 새로운 영상을 탐색중입니다...")
        target_ids = search_videos(keyword, max_result=MAX_VIDEOS)
        if not target_ids:
            print("오류 - 영상을 찾을 수 없습니다.")
            return

    print("영상 데이터를 수집 및 csv에 업데이트 하는 중...")
    videos_data = video_stats(target_ids, batch_id, record_date, keyword)
    data_upload_to_csv(video_csv, videos_data)

    print("댓글 데이터를 수집 및 csv에 업데이트 하는 중...")
    comments_data = []
    for video in target_ids:
        comments_data.extend(Search_comment(video, batch_id, record_date, max_result=MAX_COMMENTS))
    data_upload_to_csv(comments_csv, comments_data)

    print(f"작업 완료! [{record_date}] 데이터 저장 성공\n")

if __name__ == "__main__":
    main()