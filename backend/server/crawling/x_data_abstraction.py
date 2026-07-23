import os
import sys

from apify_client import ApifyClient
from key_setting import apify_api_key

# 상위(server) 폴더 경로
current_dir = os.path.dirname(os.path.realpath(__file__))
top_level_dir = os.path.dirname(current_dir)
if top_level_dir not in sys.path:
    sys.path.append(top_level_dir)

def get_X_data(keyword, max_items):
    client = ApifyClient(token=apify_api_key)

    query_list = [keyword]
    if not keyword.startswith('#'):
        query_list.append(f"#{keyword}")

    print(f"{keyword} 검색 데이터 처리 중...")

    # 액터 명령
    run_input = {
        "searchTerms": [keyword],
        "sort": "Latest",
        "maxItems": max_items
    }

    # 액터를 작동시키고, 끝날 때까지 대기
    run = client.actor("nfp1fpt5gUlBwPcor").call(run_input = run_input)

    # 출력
    found_data = []

    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        content = item.get("text", "내용 없음").replace('\n', ' ')
        title = content[:30] + "..." if len(content) > 30 else content

        x_data = {
            "id": item.get("id", "ID 없음"),
            "title": title,
            "content": content,
            "likes": item.get("likes", item.get("favorite_count", 0)),
            "retweets": item.get("retweets", item.get("retweet_count", 0)),
            "views": item.get("views", item.get("view_count", "조회수 비공개"))
        }
        found_data.append(x_data)

    return found_data

search_keyword = input("검색할 키워드를 입력하세요: ")

if __name__ == "__main__":
    search_keyword = "테스트"
    try:
        res = get_X_data(search_keyword, max_items=5)
        for data in res:
            print(f"[id]: {data['id']}")
            print(f"[title]: {data['title']}")
            print(f"[content]: {data['content']}")
            print(f"[likes]: {data['likes']}")
            print(f"[retweets]: {data['retweets']}")
            print(f"[views]: {data['views']}")
            print("\n\n")
    except Exception as e:
        print(f"테스트 실행 에러: {e}")