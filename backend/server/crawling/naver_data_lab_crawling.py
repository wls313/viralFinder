import sys
import urllib.request
import json
import pandas as pd
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine, text

from server.config.config import host_ip, user_value, password_value, database_name
from server.key_setting import naver_client_id, naver_client_secret, naver_openapi_url

def search_keyword(keyword):
    client_id = naver_client_id
    client_secret = naver_client_secret

    kor_time = timezone(timedelta(hours=9))
    now_time = datetime.now(kor_time)
    measurement_time = now_time - timedelta(days=7)
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

            print("\n" + "-" * 20)
            print(f"{keyword} 검색량 변화 추이")
            print("\n" + "-" * 20)
            print(df.head(30))

            engine = create_engine(f"mysql+pymysql://{user_value}:{password_value}@{host_ip}/{database_name}?charset=utf8mb4")

            with engine.begin() as conn:
                conn.execute(text("INSERT IGNORE INTO keyword (target_keyword) VALUES (:kw)"), {"kw": keyword})
                keyword_id = conn.execute(text("SELECT keyword_id FROM keyword WHERE target_keyword = :kw"), {"kw": keyword}).fetchone()[0]

            df = df.rename(columns={'측정 기간': 'period', '상대적 비율': 'relative_ratio'})
            df['keyword_id'] = keyword_id

            df[['keyword_id', 'period', 'relative_ratio']].to_sql(
                name='naver',
                con=engine,
                if_exists='append',
                index=False
            )

            print(f"{keyword} 저장 완료!")

        else:
            print(f"API 호출 실패(에러코드 - {response.getcode()})")

    except Exception as e:
        print(f"오류가 발생했습니다: {e}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        keyword = sys.argv[1]
    else:
        keyword = input("키워드를 입력하세요: ").strip()

    search_keyword(keyword)