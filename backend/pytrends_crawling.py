import pandas as pd
from pytrends.request import TrendReq
import time
from datetime import datetime, timedelta, timezone

def search_keyword(keyword, max_retries=3):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    pytrends = TrendReq(hl='ko-KR', tz=540, requests_args={'headers':{'User-Agent':user_agent}})

    kor_time = timezone(timedelta(hours=9))
    now_time = datetime.now(kor_time)
    measurement_time = now_time - timedelta(days=90)
    start_date = measurement_time.strftime('%Y-%m-%d')
    end_date = now_time.strftime('%Y-%m-%d')
    time_unit = "date"

    for attempt in range(1, max_retries + 1):
        try:
            timeframe = f"{start_date} {end_date}"
            pytrends.build_payload(kw_list=[keyword], timeframe=timeframe, geo='KR')

            df = pytrends.interest_over_time()

            if df.empty:
                print("데이터가 없습니다.")
                return

            if 'isPartial' in df.columns:
                # isPartial : 불완전 데이터 여부
                df = df.drop(columns=['isPartial'])

            df = df.reset_index()

            df = df.rename(columns={'date':'측정 기간', keyword: '상대적 비율'})

            df.insert(0, '키워드', keyword)

            print("\n" + "-" * 20)
            print(f"'{keyword}' 검색량 변화 추이")
            print("-" * 20)
            print(df.head(20))

            filename = f"{keyword}_google_trends.csv"
            with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
                f.write(f"{start_date},{end_date},{time_unit}\n")
                df.to_csv(f, index=False)

            print(f"{filename} 저장 완료!")
            break

        except Exception as e:
            err_msg = str(e)

            # 에러코드 429(구글 임시 차단)이 발생할 경우
            if "429" in err_msg:
                if attempt < max_retries:
                    wait_time = 20 * attempt
                    print(f"에러코드 429 - {wait_time}초 대기 후 재시도({attempt}/{max_retries}회 시도 중)")
                    time.sleep(wait_time)
                else:
                    print("잠시후 다시 시도해주십시오")
            else:
                print(f"오류가 발생했습니다: {e}")
                break


if __name__ == '__main__':
    keyword = input("키워드를 입력하세요: ")
    search_keyword(keyword)