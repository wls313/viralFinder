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

from config.config import host_ip, user_value, password_value, database_name
from key_setting import DB_CONFIG


def search_keyword(keyword, search_range, max_retries=3):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    pytrends = TrendReq(hl='ko-KR', tz=540, requests_args={'headers':{'User-Agent':user_agent}})

    kor_time = timezone(timedelta(hours=9))
    now_time = datetime.now(kor_time)
    created_time = now_time.strftime("%Y-%m-%d %H:%M:%S")

    measurement_time = now_time - timedelta(days=search_range)
    start_date = measurement_time.strftime('%Y-%m-%d')
    end_date = now_time.strftime('%Y-%m-%d')

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
                username=user_value,
                password=password_value,
                host=host_ip,
                database=database_name,
                query={"charset": "utf8mb4"}
            )

            engine = create_engine(db_url)

            with engine.begin() as conn:
                conn.execute(text("INSERT IGNORE INTO keyword (target_keyword) VALUES (:kw)"), {"kw": keyword})
                keyword_id = conn.execute(text("SELECT keyword_id FROM keyword WHERE target_keyword = :kw"), {"kw": keyword}).fetchone()[0]

            df['search_range'] = search_range
            df['created_at'] = created_time
            df['keyword_id'] = keyword_id

            result_data = df[['period', 'relative_ratio']].to_dict(orient='records')

            try:
                df[['keyword_id', 'period', 'relative_ratio', 'created_at', 'search_range']].to_sql(
                    name='google',
                    con=engine,
                    if_exists='append',
                    index=False
                )
                db_message = "데이터베이스를 성공적으로 저장하였습니다."
            except Exception as db_e:
                db_message = f"데이터베이스 저장 실패 혹은 중복 데이터가 발생했습니다. : {str(db_e)}"

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
    keyword = sys.argv[1] if len(sys.argv) > 1 else "무중력"
    search_range = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    search_keyword(keyword, search_range)