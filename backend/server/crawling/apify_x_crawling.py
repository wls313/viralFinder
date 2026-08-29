import os, sys
import pymysql

from apify_client import ApifyClient
from datetime import datetime, timedelta

current_dir = os.path.dirname(os.path.realpath(__file__))
top_level_dir = os.path.dirname(current_dir)
if top_level_dir not in sys.path:
    sys.path.append(top_level_dir)

from config.database import get_keyword_id
from config.config import apify_api_key, DB_CONFIG

client = ApifyClient(apify_api_key)
TWITS_NUM = 5
SEARCHING_TWEETS_COUNTS = 10
DEFAULT_SEARCH_RANGE = 1

def get_db_connection():
    return pymysql.connect(host=DB_CONFIG["host"], user=DB_CONFIG["user"], password=DB_CONFIG["password"], database=DB_CONFIG["database"],
                           charset=DB_CONFIG["charset"])

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

def search_x(keyword, search_range):
    keyword_id = get_keyword_id(keyword)
    START_DATE = (datetime.now() - timedelta(weeks=search_range)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    END_DATE = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")

    run_input = {
        "searchTerms": [
            f'"{keyword}" OR "#{keyword}"'
        ],
        "maxItems": TWITS_NUM,
        "sort": "Latest",
        "includeSearchTerms": True,
        "tweetLanguage": "ko",

        "customMapFunction": "(object) => { return {...object} }",
        "proxyConfig": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"]
        },
        "start": START_DATE,
        "end": END_DATE
    }

    try:
        run = client.actor("61RPP7dywgiy0JPD0").call(run_input=run_input)
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
                    full_text = item.get("full_text") or item.get("text") or ""
                    keyword_lower = keyword.lower()
                    text_lower = full_text.lower()
                    if keyword_lower not in text_lower and f"#{keyword_lower}" not in text_lower:
                        continue

                    raw_time = item.get("createdAt")
                    created_at = datetime.strptime(raw_time, "%a %b %d %H:%M:%S +0000 %Y") if raw_time else None

                    user = item.get("author", {})

                    screen_name = user.get("userName")
                    tweet_id = item.get("id")
                    tweet_url = item.get("url") or f"https://x.com/{screen_name}/status/{tweet_id}"

                    values = (
                        tweet_id,
                        keyword_id,
                        item.get("full_text") or item.get("text"),
                        created_at,
                        user.get("userName"),
                        int(user.get("id", 0)),
                        item.get("likeCount", 0),
                        item.get("retweetCount", 0),
                        item.get("replyCount", 0),
                        item.get("quoteCount", 0),
                        item.get("viewCount", 0),
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
        run = client.actor("61RPP7dywgiy0JPD0").start(run_input=run_input)
        client.run(run["id"]).wait_for_finish()
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql_query = """
                    insert into recommend (type, url, content, published_date) values (%s, %s, %s, %s)
                    on duplicate key update content = VALUES(content)       
                """

                for item in items:
                    raw_time = item.get("createdAt")
                    created_at = datetime.strptime(raw_time, "%a %b %d %H:%M:%S +0000 %Y") if raw_time else None

                    user = item.get("author", {})
                    screen_name = user.get("userName")
                    tweet_id = item.get("id")

                    tweet_url = item.get("url") or f"https://x.com/{screen_name}/status/{tweet_id}"
                    full_text = item.get("fullText") or item.get("text")

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
    '''
    keyword = input("검색할 키워드를 입력하세요: ")
    search_range = input("검색할 기간(week)를 입력하세요: ")
    '''
    keyword = sys.argv[1] if len(sys.argv) > 1 else "버터쿠키"
    search_range = int(sys.argv[2] if len(sys.argv) > 2 else 1)

    search_x(keyword, search_range)

    print(f"{keyword}에 대한 X 데이터 수집을 완료했습니다.")

if __name__ == '__main__':
    run_x_search()