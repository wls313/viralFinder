import pymysql
import pandas as pd
from .config import DB_CONFIG

def get_or_create_keyword_id(conn, keyword_name):
    with conn.cursor() as cursor:
        sql = "SELECT keyword_id FROM keyword WHERE target_keyword = %s;"
        cursor.execute(sql, (keyword_name,))
        result = cursor.fetchone()
        if result:
            return result[0]

        sql = "INSERT IGNORE INTO keyword (target_keyword) VALUES (%s);"
        cursor.execute(sql, (keyword_name,))
        conn.commit()

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
            keyword_id = get_or_create_keyword_id(conn, keyword_name_or_id)

        if not keyword_id:
            return pd.DataFrame(), pd.DataFrame(), None

        trend_query = """
                      SELECT
                          n.period,
                          n.relative_ratio AS weight_naver,
                          IFNULL(g.relative_ratio, 0) AS weight_google,
                          IFNULL(t.relative_ratio, 0) AS weight_twitter
                      FROM naver n
                               LEFT JOIN google g ON n.keyword_id = g.keyword_id AND n.period = g.period
                               LEFT JOIN twitter t ON n.keyword_id = t.keyword_id AND n.period = t.period
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