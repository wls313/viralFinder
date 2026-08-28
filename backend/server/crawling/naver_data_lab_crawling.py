import os, sys
import urllib.request
import json
import pandas as pd
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# 상위(server) 폴더 경로
current_dir = os.path.dirname(os.path.realpath(__file__))
top_level_dir = os.path.dirname(current_dir)
if top_level_dir not in sys.path:
    sys.path.append(top_level_dir)

from config.config import DB_CONFIG, naver_client_id, naver_client_secret, naver_openapi_url

def search_keyword(keyword, search_range):
    client_id = naver_client_id
    client_secret = naver_client_secret

    kor_time = timezone(timedelta(hours=9))
    now_time = datetime.now(kor_time)
    created_time = now_time.strftime('%Y-%m-%d %H:%M:%S')

    measurement_time = now_time - timedelta(days=search_range)
    start_date = measurement_time.strftime('%Y-%m-%d')
    end_date = now_time.strftime('%Y-%m-%d')
    time_unit = "date"

    url = naver_openapi_url

    body = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": time_unit,
        "keywordGroups": [{"groupName": keyword, "keywords": [keyword]}]
    }

    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    request.add_header("Content-Type", "application/json")

    try:
        response = urllib.request.urlopen(request, data = json.dumps(body).encode("utf-8"))

        if response.getcode() == 200:
            data = json.loads(response.read().decode("utf-8"))

            crawling_data = []
            for result in data["results"]:
                group_name = result["title"]
                for item in result["data"]:
                    crawling_data.append([group_name, item["period"], item['ratio']])

            df = pd.DataFrame(crawling_data, columns=["키워드", "측정 기간", "상대적 비율"])

            db_url = URL.create(
                drivername="mysql+pymysql",
                username=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                host=DB_CONFIG["host"],
                database=DB_CONFIG["database"],
                query=DB_CONFIG["charset"]
            )
            engine = create_engine(db_url)
            with engine.begin() as conn:
                conn.execute(text("INSERT IGNORE INTO keyword (target_keyword) VALUES (:kw)"), {"kw": keyword})
                keyword_id = conn.execute(text("SELECT keyword_id FROM keyword WHERE target_keyword = :kw"), {"kw": keyword}).fetchone()[0]

            df = df.rename(columns={'측정 기간': 'period', '상대적 비율': 'relative_ratio'})
            df['keyword_id'] = keyword_id
            df['search_range'] = search_range
            df['created_at'] = created_time

            try:
                df[['keyword_id', 'search_range', 'period', 'relative_ratio', 'created_at']].to_sql(
                    name='naver',
                    con=engine,
                    if_exists='append',
                    index=False
                )
                db_message = "데이터베이스에 성공적으로 저장하였습니다."

            except Exception as db_e:
                db_message = f"데이터베이스 저장 실패 혹은 중복 데이터가 발생했습니다. : {str(db_e)}"

            result_data = df[['period', 'relative_ratio']].to_dict(orient='records')

            print(json.dumps({
               "status": "success",
                "keyword": keyword,
                "current_date": end_date,
                "search_range": search_range,
                "db_message": db_message,
                "data": result_data
            }, ensure_ascii=False))

        else:
            print(json.dumps({
                "status": "error",
                "keyword": keyword,
                "message": f"네이버 데이터랩 API를 호출하는데 실패했습니다. : ({response.getcode()})"
            }, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({
            "status": "error",
            "keyword": keyword,
            "message": str(e),
        }, ensure_ascii=False))

if __name__ == '__main__':
    keyword = sys.argv[1] if len(sys.argv) > 1 else ""
    search_range = int(sys.argv[2]) if len(sys.argv) > 2 else 90

    if keyword:
        search_keyword(keyword, search_range)
    else:
        # search_keyword("아아", 90)
        print(json.dumps({"status": "error", "message": "naver 에러: 키워드를 전달받지 못했습니다."}))