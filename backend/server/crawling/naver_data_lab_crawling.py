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

from config.config import DB_CONFIG, DB_URL, naver_client_id, naver_client_secret, naver_openapi_url

def search_keyword(keyword, search_range):
    client_id = naver_client_id
    client_secret = naver_client_secret

    kor_time = timezone(timedelta(hours=9))
    now_time = datetime.now(kor_time)
    created_time = now_time.strftime('%Y-%m-%d %H:%M:%S')

    yesterday = now_time - timedelta(days=1)
    end_date = yesterday.strftime('%Y-%m-%d')
    measurement_time = yesterday - timedelta(days=search_range)
    start_date = measurement_time.strftime('%Y-%m-%d')
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

            engine = create_engine(DB_URL)
            with engine.begin() as conn:
                conn.execute(text("INSERT IGNORE INTO keyword (target_keyword) VALUES (:kw)"), {"kw": keyword})
                keyword_id = conn.execute(text("SELECT keyword_id FROM keyword WHERE target_keyword = :kw"), {"kw": keyword}).fetchone()[0]

            df = df.rename(columns={'측정 기간': 'period', '상대적 비율': 'relative_ratio'})
            df['keyword_id'] = keyword_id
            df['search_range'] = search_range
            df['created_at'] = created_time

            # 90일
            # z-score
            df['z_score_90'] = ((df['relative_ratio'] - df['relative_ratio'].mean()) / df['relative_ratio'].std()).fillna(0)
            # t-score (검색 급상승량 지표)
            df['t_score_90'] = 50 + df['z_score_90'] * 10
            # t-score 백분율 (프론트엔드 출력용 검색 급상승량 지표)
            df['t_score_percentage_90'] = df['t_score_90'].clip(0, 100).round(1)

            t_score_90 = df.iloc[-1]['t_score_90']
            prev_90 = df.iloc[-2]['t_score_90'] if len(df) > 1 else t_score_90
            delta_90 = round(t_score_90 - prev_90, 1)
            pct_90 = df.iloc[-1]['t_score_percentage_90']

            # 30일
            df_30 = df.tail(30).copy()
            df_30['z_score_30'] = ((df_30['relative_ratio'] - df_30['relative_ratio'].mean()) / df_30['relative_ratio'].std()).fillna(0)
            df_30['t_score_30'] = 50 + df_30['z_score_30'] * 10
            df_30['t_score_percentage_30'] = df_30['t_score_30'].clip(0, 100).round(1)

            t_score_30 = df_30.iloc[-1]['t_score_30']
            prev_30 = df_30.iloc[-2]['t_score_30'] if len(df_30) > 1 else t_score_30
            delta_30 = round(t_score_30 - prev_30, 1)
            pct_30 = df_30.iloc[-1]['t_score_percentage_30']

            # 7일
            df_7 = df.tail(7).copy()
            df_7['z_score_7'] = ((df_7['relative_ratio'] - df_7['relative_ratio'].mean()) / df_7['relative_ratio'].std()).fillna(0)
            df_7['t_score_7'] = 50 + df_7['z_score_7'] * 10
            df_7['t_score_percentage_7'] = df_7['t_score_7'].clip(0, 100).round(1)

            t_score_7 = df_7.iloc[-1]['t_score_7']
            prev_7 = df_7.iloc[-2]['t_score_7'] if len(df_7) > 1 else t_score_7
            delta_7 = round(t_score_7 - prev_7, 1)
            pct_7 = df_7.iloc[-1]['t_score_percentage_7']

            if int(search_range) == 90:
                try:
                    with engine.begin() as conn:
                        df_insert = df[['keyword_id', 'search_range', 'period', 'relative_ratio', 'z_score_90', 't_score_90', 'created_at']].rename(columns={'z_score_90': 'z_score', 't_score_90': 't_score'})
                        insert_data = df_insert.to_dict(orient='records')

                        upsert_sql = text("""
                            INSERT INTO naver (keyword_id, search_range, period, relative_ratio, z_score, t_score, created_at)
                            VALUES (:keyword_id, :search_range, :period, :relative_ratio, :z_score, :t_score, :created_at)
                            ON DUPLICATE KEY UPDATE relative_ratio = VALUES(relative_ratio), z_score = VALUES(z_score),t_score = VALUES(t_score), search_range = VALUES(search_range), created_at = VALUES(created_at)
                        """)
                        conn.execute(upsert_sql, insert_data)

                        update_keyword_sql = text("""
                            UPDATE keyword 
                            SET naver_t_score_90 = :t90, naver_delta_90 = :d90, naver_t_score_30 = :t30, naver_delta_30 = :d30, naver_t_score_7  = :t7,  naver_delta_7  = :d7
                            WHERE target_keyword = :keyword
                        """)

                        conn.execute(update_keyword_sql, {
                            "t90": pct_90, "d90": delta_90,
                            "t30": pct_30, "d30": delta_30,
                            "t7":  pct_7,  "d7":  delta_7,
                            "keyword": keyword
                        })

                        db_message = "데이터베이스에 성공적으로 추가/업데이트 하였습니다."

                except Exception as db_e:
                    db_message = f"데이터베이스 저장 실패 혹은 중복 데이터가 발생했습니다. : {str(db_e)}"

            else:
                db_message = f"90일치 데이터가 아니기에 DB 저장은 건너뜁니다."

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
        # search_keyword("Hello World", 90)
        print(json.dumps({"status": "error", "message": "naver 에러: 키워드를 전달받지 못했습니다."}))