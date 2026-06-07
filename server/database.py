import pymysql
import pandas as pd
from config import DB_CONFIG

def get_keyword_id(conn, keyword_name):
    """사용자가 입력한 텍스트(예: 차지티)로 keyword_id를 찾아오는 함수"""
    with conn.cursor() as cursor:
        sql = "SELECT keyword_id FROM analysis_keyword WHERE target_keyword = %s;"
        cursor.execute(sql, (keyword_name,))
        result = cursor.fetchone()
        return result[0] if result else None

def fetch_data(keyword_name_or_id):
    """숫자 ID나 문자열 키워드명 모두 대응하여 데이터를 로드"""
    conn = pymysql.connect(**DB_CONFIG)
    try:
        # 1. 입력값이 숫자인지 글자인지 판별하여 keyword_id 추출
        if str(keyword_name_or_id).isdigit():
            keyword_id = int(keyword_name_or_id)
        else:
            keyword_id = get_keyword_id(conn, keyword_name_or_id)

        # DB에 없는 키워드면 빈 데이터프레임 반환
        if not keyword_id:
            return pd.DataFrame(), pd.DataFrame(), None

        # 2. 데이터 조회 쿼리 실행
        trend_query = """
                      SELECT
                          n_detail.period,
                          (n_detail.relative_ratio * n_master.application_ratio) AS weight_naver,
                          (g_detail.relative_ratio * g_master.application_ratio) AS weight_google
                      FROM naver_datalab_detail n_detail
                               JOIN naver_datalab_master n_master ON n_detail.master_id = n_master.master_id
                               JOIN google_trend_detail g_detail ON n_detail.period = g_detail.period
                               JOIN google_trend_master g_master ON g_detail.master_id = g_master.master_id
                      WHERE n_master.keyword_id = %s AND g_master.keyword_id = %s; \
                      """
        video_query = """
                      SELECT
                          video_id,
                          caption_name,
                          DATE(uploaded_at) AS uploaded_date,
                          positive_ratio,
                          view_count
                      FROM youtube_video
                      WHERE keyword_id = %s; \
                      """

        trend_df = pd.read_sql(trend_query, conn, params=(keyword_id, keyword_id))
        video_df = pd.read_sql(video_query, conn, params=(keyword_id,))

        if not trend_df.empty:
            trend_df["period"] = pd.to_datetime(trend_df["period"])
        if not video_df.empty:
            video_df["uploaded_date"] = pd.to_datetime(video_df["uploaded_date"])

        return trend_df, video_df, keyword_id
    finally:
        conn.close()