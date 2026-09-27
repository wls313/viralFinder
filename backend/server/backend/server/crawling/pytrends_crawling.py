import os
import sys
import json
from pytrends.request import TrendReq
import time
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from datetime import datetime, timedelta, timezone

# 상위(server) 폴더 경로
current_dir = os.path.dirname(os.path.realpath(__file__))
top_level_dir = os.path.dirname(current_dir)
if top_level_dir not in sys.path:
    sys.path.append(top_level_dir)

from config.config import DB_CONFIG


def search_keyword(keyword, search_range, max_retries=3):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    pytrends = TrendReq(hl='ko-KR', tz=540, requests_args={'headers':{'User-Agent':user_agent}})

    kor_time = timezone(timedelta(hours=9))
    now_time = datetime.now(kor_time)
    created_time = now_time.strftime("%Y-%m-%d %H:%M:%S")

    yesterday = now_time - timedelta(days=1)
    measurement_time = now_time - timedelta(days=search_range + 1)
    start_date = measurement_time.strftime('%Y-%m-%d')
    end_date = yesterday.strftime('%Y-%m-%d')

    for attempt in range(1, max_retries + 1):
        try:
            timeframe = f"{start_date} {end_date}"
            pytrends.build_payload(kw_list=[keyword], timeframe=timeframe, geo='KR')

            df = pytrends.interest_over_time()

            if df.empty:
                print(json.dumps({
                    "status": "success",
                    "keyword": keyword,
                    "search_range": search_range,
                    "db_message": "가져올 데이터가 없습니다.",
                    "data": []
                }, ensure_ascii=False))
                return

            if 'isPartial' in df.columns:
                df = df.drop(columns=['isPartial'])

            df = df.reset_index()
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')
            df = df.rename(columns={'date':'period', keyword: 'relative_ratio'})

            db_url = URL.create(
                drivername="mysql+pymysql",
                username=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                host=DB_CONFIG["host"],
                database=DB_CONFIG["database"],
                query={"charset" : DB_CONFIG["charset"]}
            )
            engine = create_engine(db_url)
            with engine.begin() as conn:
                conn.execute(text("INSERT IGNORE INTO keyword (target_keyword) VALUES (:kw)"), {"kw": keyword})
                keyword_id = conn.execute(text("SELECT keyword_id FROM keyword WHERE target_keyword = :kw"), {"kw": keyword}).fetchone()[0]

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


            result_data = df[['period', 'relative_ratio']].to_dict(orient='records')

            if int(search_range) == 90:
                try:
                    with engine.begin() as conn:
                        # 1. 서브 테이블(google)에 시계열 데이터 누적 (UPSERT)
                        insert_data = df[['keyword_id', 'search_range', 'period', 'relative_ratio', 'z_score_90', 't_score_90', 'created_at']] \
                            .rename(columns={'z_score_90': 'z_score', 't_score_90': 't_score'}) \
                            .to_dict(orient='records')

                        upsert_sql = text("""
                            INSERT INTO google (keyword_id, search_range, period, relative_ratio, z_score, t_score, created_at)
                            VALUES (:keyword_id, :search_range, :period, :relative_ratio, :z_score, :t_score, :created_at)
                            ON DUPLICATE KEY UPDATE relative_ratio = VALUES(relative_ratio), z_score = VALUES(z_score), t_score = VALUES(t_score), search_range = VALUES(search_range), created_at = VALUES(created_at)
                        """)
                        conn.execute(upsert_sql, insert_data)

                        # 2. 메인 테이블(keyword)에 구글 최신 전광판 갱신 (UPDATE)
                        update_keyword_sql = text("""
                            UPDATE keyword 
                            SET google_t_score_90 = :t90, google_delta_90 = :d90,
                                google_t_score_30 = :t30, google_delta_30 = :d30,
                                google_t_score_7  = :t7,  google_delta_7  = :d7
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

            print(json.dumps({
                "status": "success",
                "keyword": keyword,
                "search_range": search_range,
                "db_message": db_message,
                "data": result_data
            }, ensure_ascii=False))

            return

        except Exception as e:
            err_msg = str(e)
            # 에러코드 429(구글 임시 차단)이 발생할 경우
            if "429" in err_msg:
                if attempt < max_retries:
                    wait_time = 20 * attempt
                    sys.stderr.write(f"에러코드 429 - {wait_time}초 대기 후 재시도({attempt}/{max_retries}회 시도 중)\n")
                    time.sleep(wait_time)
                else:
                    print(json.dumps({
                        "status": "error",
                        "keyword": keyword,
                        "message": "잠시 후 다시 시도해주세요"
                    }, ensure_ascii=False))
                    return
            else:
                print(json.dumps({
                    "status": "error",
                    "keyword": keyword,
                    "message": f"오류가 발생했습니다! : {err_msg}"
                }, ensure_ascii=False))
                return

if __name__ == '__main__':
    keyword = sys.argv[1] if len(sys.argv) > 1 else ""
    search_range = int(sys.argv[2]) if len(sys.argv) > 2 else 90

    if keyword:
        search_keyword(keyword, search_range)
    else:
        # search_keyword("Hello World", 90)
        print(json.dumps({"status": "error", "message": "google 에러: 키워드를 전달받지 못했습니다."}))