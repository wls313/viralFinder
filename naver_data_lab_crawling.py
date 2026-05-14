import os
import sys
import urllib.request
import json
import pandas as pd

def search_keyword(keyword):
    client_id = "Or44GhFkSQ6ld3by3_tx"
    client_secret = "5fgc908_KF"

    start_date = "2026-01-01"
    end_date = "2026-05-11"
    time_unit = "date"
    url = "https://openapi.naver.com/v1/datalab/search"

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