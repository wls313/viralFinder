import os, sys
import pymysql
import pandas as pd

current_dir = os.path.dirname(os.path.realpath(__file__))
top_level_dir = os.path.dirname(current_dir)
if top_level_dir not in sys.path:
    sys.path.append(top_level_dir)

from config.config import DB_CONFIG


def get_keyword_id(keyword_name: str):
    """키워드 이름을 받아 keyword_id를 반환 (없으면 INSERT)"""
    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            cursor.execute("INSERT IGNORE INTO keyword (target_keyword) VALUES (%s);", (keyword_name,))
            conn.commit()
            cursor.execute("SELECT keyword_id FROM keyword WHERE target_keyword = %s;", (keyword_name,))
            row = cursor.fetchone()
            return row[0] if row else None
    finally:
        conn.close()


def fetch_data(keyword_name_or_id):
    """트렌드 시계열 데이터 및 비디오 데이터 조회 (LEFT JOIN 적용)"""
    if str(keyword_name_or_id).isdigit():
        keyword_id = int(keyword_name_or_id)
    else:
        keyword_id = get_keyword_id(str(keyword_name_or_id))

    if not keyword_id:
        return pd.DataFrame(), pd.DataFrame(), None

    conn = pymysql.connect(**DB_CONFIG)
    try:
        # LEFT JOIN 적용하여 구글 데이터 누락 시에도 네이버 데이터 정상 반환
        trend_query = """
                      SELECT
                          n.period,
                          n.relative_ratio AS weight_naver,
                          IFNULL(g.relative_ratio, 0.0) AS weight_google
                      FROM naver n
                               LEFT JOIN google g ON n.keyword_id = g.keyword_id AND n.period = g.period
                      WHERE n.keyword_id = %s
                      ORDER BY n.period ASC;
                      """

        video_query = """
                      SELECT
                          video_id,
                          DATE(record_date) AS uploaded_date,
                          daily_view_count AS view_count
                      FROM youtube
                      WHERE keyword_id = %s;
                      """

        trend_df = pd.read_sql(trend_query, conn, params=(keyword_id,))
        video_df = pd.read_sql(video_query, conn, params=(keyword_id,))

        if not trend_df.empty:
            trend_df["period"] = pd.to_datetime(trend_df["period"])
        if not video_df.empty:
            video_df["uploaded_date"] = pd.to_datetime(video_df["uploaded_date"])

        return trend_df, video_df, keyword_id

    finally:
        conn.close()