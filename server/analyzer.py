import logging
import warnings
import numpy as np
import pandas as pd
import pymysql

warnings.filterwarnings("ignore", category=UserWarning)

# 로그 출력 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

# DB
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "1234",
    "database": "viralFinder",
    "charset": "utf8mb4",
}

def fetch_data(conn, keyword_id):
    # 정규화
    trend_query = """
                  SELECT
                      n_detail.period,
                      (n_detail.relative_ratio * n_master.application_ratio) AS weight_naver,
                      (g_detail.relative_ratio * g_master.application_ratio) AS weight_google
                  FROM naver_datalab_detail n_detail
                           JOIN naver_datalab_master n_master ON n_detail.master_id = n_master.master_id
                           JOIN google_trend_detail g_detail ON n_detail.period = g_detail.period
                           JOIN google_trend_master g_master ON g_detail.master_id = g_master.master_id
                  WHERE n_master.keyword_id = %s AND g_master.keyword_id = %s \
                  """
    #유튜브 데이터 조회
    video_query = """
                  SELECT
                      video_id,
                      caption_name,
                      DATE(uploaded_at) AS uploaded_date,
                      positive_ratio,
                      view_count
                  FROM youtube_video
                  WHERE keyword_id = %s \
                  """


    trend_df = pd.read_sql(trend_query, conn, params=(keyword_id, keyword_id))
    video_df = pd.read_sql(video_query, conn, params=(keyword_id,))

    if not trend_df.empty:
        trend_df["period"] = pd.to_datetime(trend_df["period"])
    if not video_df.empty:
        video_df["uploaded_date"] = pd.to_datetime(video_df["uploaded_date"])

    return trend_df, video_df


def analyze_viral_traffic(trend_df, video_df):
    #IQR과 Z-Score 기반 통계적 이상치 탐지 알고리즘 연산 함수
    trend_df["interest_raw"] = (trend_df["weight_naver"] * 0.65) + (
            trend_df["weight_google"] * 0.35
    )

    # Z-Score 정규화 (Standardization)
    # 다른 스케일을 가진 데이터들을 평균 0, 표준편차 1 분포로 표준화하여
    # 특정 날짜의 검색량이 전체 평균 대비 얼마나 과열되었는지 객체 간 상대적 지표로 정형화함
    trend_mean = trend_df["interest_raw"].mean()
    trend_std = trend_df["interest_raw"].std()

    # 제로 디비전(Zero Division) 방지 및 결측치 방어 로직
    if trend_std == 0 or pd.isna(trend_std):
        trend_std = 1.0

    trend_df["interest_z"] = (trend_df["interest_raw"] - trend_mean) / trend_std

    analysis_results = []

    for _, video in video_df.iterrows():
        upload_date = video["uploaded_date"]
        matched_trend = trend_df[trend_df["period"] == upload_date]

        # 트렌드 데이터가 누락된 경우, 원본 점수 보존을 위해 Z-Score를 0.0(평균)으로 수렴시킴
        z_interest = (
            matched_trend["interest_z"].values[0]
            if not matched_trend.empty
            else 0.0
        )

        # 지수적 페널티 (Exponential Penalty) 적용
        # Z-Score를 자연상수 e의 지수로 치환하여 분모에 배치함으로써, 대중의 실질적 검색(관심도)
        # 평균 이상으로 상승할경우 분모가 증가하게 만듦.
        # 이를 통해 진짜 유행으로 흥행한 유튜브의 점수를 억제하고 바이럴 영상을 강력하게 격리함.

        # 1. 표준 시그모이드 함수 정의 (0 ~ 1 사이로 압축)
        sigmoid_val = 1 / (1 + np.exp(-z_interest))

        # 2. 페널티 완화 스케일링 (분모의 범위를 1.0 ~ 5.0 사이로 제한)
        # 검색량이 최악일 때는 분모가 1 (원본 점수 유지)
        # 검색량이 무한대로 폭발해도 분모는 최대 5 (점수가 최소 5분의 1은 보존됨)
        denominator = 1.0 + 4.0 * sigmoid_val

        # 3. 최종 스코어 연산
        score = video["positive_ratio"] / denominator

        analysis_results.append(
            {
                "video_id": video["video_id"],
                "title": video["caption_name"],
                "positive_ratio": video["positive_ratio"],
                "z_interest": round(z_interest, 2),
                "score": round(score, 2),
                "status": "대기",
            }
        )

    result_df = pd.DataFrame(analysis_results)

    if result_df.empty:
        return result_df

    # IQR 기반 동적 경계선 산출
    # 고정 임계값(Hard-coded limit) 대신, 획득한 이상치 데이터 분포의 상위 75% 지점(Q3)과
    # 하위 25% 지점(Q1)의 격차인 IQR을 연산하여, 데이터 자체의 스케일에 따라
    # '바이럴 주의' 및 '바이럴 의심' 판정 기준선을 유연하고 동적으로 정의함 (통계적 이상치 탐지의 표준 방식)

    q1 = result_df["score"].quantile(0.25)
    q3 = result_df["score"].quantile(0.75)
    iqr = q3 - q1

    warning_bound = q3 + (0.2 * iqr)
    suspect_bound = q3 + (0.6 * iqr)

    if suspect_bound > 60.0:
        suspect_bound = 60.0
    if warning_bound > 35.0:
        warning_bound = 35.0

    conditions = [
        (result_df["score"] > suspect_bound),
        (result_df["score"] > warning_bound)
        & (result_df["score"] <= suspect_bound),
        (result_df["score"] <= warning_bound),
        ]
    choices = ["바이럴 의심", "바이럴 주의", "정상"]

    result_df["status"] = np.select(conditions, choices, default="정상")

    # 원본 점수와 정규화 지표를 콘솔에서 함께 검증할 수 있도록 컬럼 유지
    return result_df[
        ["video_id", "title", "positive_ratio", "z_interest", "score", "status"]
    ]


def main(keyword_id):
    # 실행부
    conn = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        trend_df, video_df = fetch_data(conn, keyword_id)

        if trend_df.empty or video_df.empty:
            logging.warning(
                f"Keyword ID {keyword_id}: 분석에 필요한 데이터가 부족합니다."
            )
            return

        result_df = analyze_viral_traffic(trend_df, video_df)

        # 콘솔 출력 포맷팅
        print(f"\n========================================================")
        print(f" 분석 결과")
        print(result_df.to_string(index=False))
        print(f"\n========================================================")

    except Exception as e:
        logging.error(f"분석 파이프라인 가동 중 실패: {e}")

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    # 테스트할 키워드 ID 입력 후 가동
    main(keyword_id=1)

# 가짜 리뷰를 찾는 평점 매크로 등에서 샤옹되는 메커니즘을 이용한 바이럴 계산식입니다.
# 바이럴 계산식 정리
# 1. 데이터들을 평균 0 표준편차 1 분포로 표준화 하여 특정 날짜의 검색량이 전체 평균 대비 얼마나 많아졌는지 객체간 상대적 지표로 정형화
# Z-score를 거치면 데이터는 평균적으로 -3 ~ +3 사이의 숫자로 압축이 됩니다 평균적인 수준이면 0이 되고 평균보다 높으면 +1 +2 +3 상승하게 되고 평균보다 적으면 -1 -2 -3 으로 감소하게됩니다.

# 2. Z-score를 자연상수 e 로 치환해 대중의 실질적 검색이 평균일상으로 조금만 상승해도 기하급수적으로 증가시켜 순수대중성으로 흥행한 영상의 점수를 억제하고 바이럴 영상을 격리함
# 자연상수 e 의 사용 이유
# ex)
# Z-score 의 값이
# x = -2 -> 평소보다 검색량이 매우 적음 분모는 0.13 정도가 됨  분모가 극도로 작아져서 바이럴 예상 점수가 7.4배 폭등 (바이럴로 의심하기 딱 좋음)
# x = 0 -> 딱 평소만큼의 검색량 분모는 1.0 원본점수(긍정 비율) 그대로 유자
# x = 1 -> 평소보다 검색량이 살짝 높음 분모는 2.71 점수가 3분의 1토막으로 깎임 (바이럴 확률 감소)
# x = 2 -> 검색량이 많이 튐 (흥행중) 분모는 7.38 점수가 7.4분의 1토막이난다.

# 였으나 너무 극단적으로 폭발시키면 안될것같기 때문에 시그모이드를 활용한 분모 페널티 완화했습니다
# 이로인해 검색량이 조금만 늦어도 점수가 박살나는 대형 유튜브 채널의 영상 탐지 불가하던 단점을 해소했습니다.


# 긍정비율을 사용하기 때문에 댓글을 필터링 할때 먼저 상품 관련 도메인 키워드를 필터링 한 후 감성분석을 들어가야 상품에 대한 제대로된 여론을 확인 가능할것같습니다.
# 구매 , 제품 , 가격, 추천 같은 단어들이 들어간것을 먼저 필터링 한 후 긍정/부정 나누기

# 3. 바이럴의 기준이 되는 고정 임계값 대신 획득한 이상치 데이터 분포의 75% (Q3)와 하위 25% (Q1)의 격차인 IQR 을 연산하여 데이터의 스케일에 따라 바이럴인지 아닌지의 판정선을 유연하고 동적으로 정의 (통계적 이상치 탐지의 표준 방식)
# 데이터가 무더기로 유입될 경우 통계적 착시로 인해 탐지력이 무너지는것을 방지하기 위해 상한선 제어 매커니즘을 결합햇습니다.