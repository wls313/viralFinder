import os, sys
import pymysql

from apify_client import ApifyClient
from datetime import datetime
from config.database import get_keyword_id

current_dir = os.path.dirname(os.path.realpath(__file__))
top_level_dir = os.path.dirname(current_dir)
if top_level_dir not in sys.path:
    sys.path.append(top_level_dir)

from key_setting import apify_api_key, host_ip, user_value, password_value, database_name

client = ApifyClient(apify_api_key)
TWITS_NUM = 5
START_DATE = None # 현재 시간
END_DATE = None # 2주 전
SEARCHING_TWEETS_COUNTS = 10

def get_db_connection():
    return pymysql.connect(host=host_ip, user=user_value, password=password_value, database=database_name,
                           charset='utf8mb4')

# 키워드 ID 조회 및 Insert
def get_keyword_id(keyword):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("INSERT IGNORE INTO keyword (target_keyword) VALUES (%s)", (keyword,))
            conn.commit()

            cursor.execute("SELECT keyword_id FROM keyword WHERE target_keyword=%s", (keyword,))
            result = cursor.fetchone()

            if result:
                return result[0]
            else:
                raise Exception(f"keyword로부터 '{keyword}' 키워드를 조회하는데 실패했습니다!")
    finally:
        conn.close()

def get_X_data(keyword, max_items=TWITS_NUM , **kwargs):
    keyword_id = get_keyword_id(keyword)

    run_input = {
        "searchTerms": [
            f"{keyword} OR #{keyword}"
        ],
        "maxItems": max_items,
        "sort": "Latest",
        "includeSearchTerms": True,
        "tweetLanguage": "ko",

        "customMapFunction": "(object) => { return {...object} }",
        "proxyConfig": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"]
        },

    }
    if START_DATE:
        run_input["start"] = START_DATE
    if END_DATE:
        run_input["end"] = END_DATE

    items = []
    
    try:
        run_handle = client.actor("61RPP7dywgiy0JPD0").call(run_input=run_input)
        run = client.run(run_handle["id"]).wait(timeout_secs=180)

        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql_query = """
                    INSERT INTO x_tweet (tweet_id, keyword_id, full_text, created_at, screen_name, user_id, favorite_count, retweet_count, reply_count, quote_count, view_count, url) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE favorite_count = VALUES(favorite_count), retweet_count = VALUES(retweet_count), view_count=VALUES(view_count)
                """

                for item in items:
                    raw_time = item.get("created_at")
                    created_at = datetime.strptime(raw_time, "%a %b %d %H:%M:%S +0000 %Y") if raw_time else None

                    user = item.get("user", {})

                    screen_name = user.get("screen_name")
                    tweet_id = item.get("id_str")
                    tweet_url = item.get("url") or f"https://x.com/{screen_name}/status/{tweet_id}"

                    values = (
                        item.get("id_str"),
                        keyword_id,
                        item.get("full_text"),
                        created_at,
                        user.get("screen_name"),
                        int(user.get("id_str", 0)),
                        item.get("favorite_count", 0),
                        item.get("retweet_count", 0),
                        item.get("reply_count", 0),
                        item.get("quote_count", 0),
                        item.get("view_count", 0),
                        tweet_url
                    )
                    cursor.execute(sql_query, values)

                conn.commit()
                print(f"{len(items)}개의 트윗을 저장했습니다!")

        except Exception as e:
            print(f"데이터베이스를 저장하는 중 오류가 발생했습니다! : {e}")
            conn.rollback()
        finally:
            conn.close()

    except Exception as e:
        print(f"실행 중 오류가 발생했습니다: {e}")

def search_trending_tweets(tweet_count=SEARCHING_TWEETS_COUNTS):
    run_input = {
        "searchTerms": [
            "lang:ko min_likes:1500"
            # 테스트 해보고 제대로 서칭이 안되면 "lang:ko min_faves:1500"으로 시도해볼 것
        ],
        "maxItems": tweet_count,
        "sort": "Latest",
        "tweetLanguage": "ko",
        "customMapFunction": "(object) => { return {...object} }",
        "proxyConfig": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"]
        }
    }

    results=[]

    try:
        run_handle = client.actor("61RPP7dywgiy0JPD0").call(run_input=run_input)
        run = client.run(run_handle["id"]).wait(timeout_secs=180)

        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql_query = """
                    insert into recommend (type, url, content, published_date) values (%s, %s, %s, %s)
                    on duplicate key update content = VALUES(content)       
                """

                for item in items:
                    raw_time = item.get("created_at")
                    created_at = datetime.strptime(raw_time, "%a %b %d %H:%M:%S +0000 %Y") if raw_time else None

                    user = item.get("user", {})
                    screen_name = user.get("screen_name")
                    tweet_id = item.get("id_str")

                    tweet_url = item.get("url") or f"https://x.com/{screen_name}/status/{tweet_id}"
                    full_text = item.get("full_text")

                    values = (
                        "tweet",
                        tweet_url,
                        full_text,
                        created_at,
                    )
                    cursor.execute(sql_query, values)

                    results.append({
                        "type": "tweet",
                        "url": tweet_url,
                        "full_text": full_text,
                        "created_at": created_at.strftime("%a %b %d %H:%M:%S") if created_at else None
                    })
                conn.commit()
                print(f"추천 트윗을 DB에 저장하였습니다.")
        except Exception as e:
            print(f"추천 트윗을 저장하는 중 오류가 발생했습니다: {e}")
            conn.rollback()
        finally:
            conn.close()
    except Exception as e:
        print(f"API로 추천 트윗을 서칭하는 중 오류가 발생했습니다: {e}")

    return results


def run_x_search():
    keyword = input("검색할 키워드를 입력하세요: ")
    keyword_id = get_keyword_id(keyword)
    get_X_data(keyword, keyword_id)

    print(f"{keyword}에 대한 X 데이터 수집을 완료했습니다.")

if __name__ == '__main__':
    run_x_search()