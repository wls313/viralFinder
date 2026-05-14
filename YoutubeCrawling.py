from googleapiclient.discovery import build
import pandas as pd

# 테스트용 옵션
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)


API_KEY = 'AIzaSyCx-AlOUq3HNhSQkF0y33RX-5uDQcerEvM'
youtube = build('youtube', 'v3', developerKey=API_KEY)

# 비디오
def search_videos(keyword, max_result = 5):
    search_response = youtube.search().list(
        q = keyword,
        type = 'video',
        part = 'id,snippet',
        maxResults = max_result
    ).execute()

    video_ids = [item['id']['videoId'] for item in search_response['items']]

    if not video_ids:
        print('해당 키워드가 포함된 영상을 찾을 수 없습니다!')
        return

    video_response = youtube.videos().list(
        id = ','.join(video_ids),
        part = 'snippet,statistics'
    ).execute()

    videos_data = []

    for item in video_response['items']:
        snippet = item['snippet']
        statistics = item.get('statistics',{})

        videos_data.append({
            '영상id':item['id'],
            '입력한 단어': keyword,
            '조회수': int(statistics.get('viewCount', 0)),
            '좋아요': int(statistics.get('likeCount', 0)),
            '설명': snippet.get('description', ''),
            '캡션명': snippet.get('title', ''),
            '업로드 날짜': snippet.get('publishedAt', ''),
        })

    return videos_data

# 각 영상의 댓글
def Search_comment(video_id, max_result = 5):
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
               '댓글 번호': item['id'],
               '캡션명': comment.get('authorDisplayName', ''),
               '댓글 내용': comment.get('textDisplay', ''),
               '좋아요': int(comment.get('likeCount', 0))
           })

   except Exception as e:
       print(f"댓글을 가져오는 중 에러 발생")

   return comments_data

if __name__ == '__main__':
    keyword = input("키워드를 입력하십시오: ")

    videos = search_videos(keyword, max_result = 5)

    if videos:
        df_videos = pd.DataFrame(videos)
        print("검색 결과\n")
        print(df_videos[['영상id', '캡션명', '조회수', '좋아요']])
        print('-' * 20)

        all_comments = [];

        for video in videos:
            vid = video['영상id']
            comments = Search_comment(video_id = vid, max_result = 5)

            for comment in comments:
                comment['영상id'] = vid
                all_comments.append(comment)

        print('-' * 20)
        if all_comments:
            df_comments = pd.DataFrame(all_comments)
            print("\n 댓글 수집 결과:")
            print(df_comments[['영상id', '캡션명', '댓글 내용', '좋아요']])
        else:
            print("\n수집된 댓글이 없습니다.")

        df_videos.to_csv(f'youtube_videos_{keyword}.csv', index=False, encoding='utf-8-sig')
        df_comments.to_csv(f'youtube_comments_{keyword}.csv', index=False, encoding='utf-8-sig')
        print(f"파일로 저장했습니다.(영상: youtube_videos_{keyword}.csv, 댓글: youtube_comments_{keyword}.csv)")

    else:
        print("검색된 영상이 없습니다.")