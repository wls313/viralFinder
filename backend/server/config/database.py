import pymysql
import pandas as pd
from .config import DB_CONFIG

def get_keyword_id(conn, keyword_name):
    with conn.cursor() as cursor:
        sql = "SELECT keyword_id FROM keyword WHERE target_keyword = %s;"
        cursor.execute(sql, (keyword_name,))
        result = cursor.fetchone()
        return result[0] if result else None

def fetch_data(keyword_name_or_id):
    conn = pymysql.connect(**DB_CONFIG)
    try:
        if str(keyword_name_or_id).isdigit():
            keyword_id = int(keyword_name_or_id)
        else:
            keyword_id = get_db_keyword_id = get_keyword_id(conn, keyword_name_or_id)

        if not keyword_id:
            return pd.DataFrame(), pd.DataFrame(), None

        trend_query = """
                      SELECT
                          n.period,
                          n.relative_ratio AS weight_naver,
                          g.relative_ratio AS weight_google
                      FROM naver n
                               JOIN google g ON n.keyword_id = g.keyword_id AND n.period = g.period
                      WHERE n.keyword_id = %s;
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