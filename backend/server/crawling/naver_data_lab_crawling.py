import urllib.request
import json
import urllib.request
from datetime import datetime, timedelta, timezone

import pandas as pd
from key_setting import naver_client_id, naver_client_secret, naver_openapi_url


def search_keyword(keyword):
    client_id = naver_client_id
    client_secret = naver_client_secret

    kor_time = timezone(timedelta(hours=9))
    now_time = datetime.now(kor_time)
    measurement_time = now_time - timedelta(days=90)
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

            filename = f"{keyword}_naver_datalab.csv"
            with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
                f.write(f"{start_date},{end_date},{time_unit}\n")
                df.to_csv(f, index=False)

            print(f"{filename} 저장 완료!")

        else:
            print(f"API 호출 실패(에러코드 - {response.getcode()})")

    except Exception as e:
        print(f"오류가 발생했습니다: {e}")

if __name__ == '__main__':
    keyword = input("키워드를 입력하세요: ")
    search_keyword(keyword)