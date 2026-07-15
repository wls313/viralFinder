import pandas as pd
import joblib
import pymysql
from Scripts.new_youtube_data_abstraction import DEFAULT_KEYWORD

from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from key_setting import host_ip, user_value, password_value, database_name



def get_db_connection():
    return pymysql.connect(host=host_ip, user=user_value, password=password_value, database=database_name, charset='utf8mb4')

def viral_interpretation(keyword):
    print("\n바이럴 판독 시작")
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("select keyword_id from analysis_keyword where target_keyword=%s",(keyword,))
            results = cursor.fetchone()
            if not results:
                print(f"오류-DB에 {keyword} 데이터가 존재하지 않습니다.")
                return {"conclusion": "데이터 없음"}
            keyword_id = results[0]

            cursor.execute("select MAX(update_coun"
                           ""
                           "t) from youtube_video where keyword_id=%s",(keyword_id,))
            max_update_results = cursor.fetchone()
            data_gradient = max_update_results[0] if max_update_results[0] else 0

            if data_gradient < 2:
                print(f"오류-데이터가 부족합니다.")
                return {"conclusion": "데이터 부족"}

        query_latest = f"SELECT video_id, daily_view_count, daily_like_count, daily_comment_count FROM youtube_video WHERE keyword_id={keyword_id} AND update_count={data_gradient}"
        df_latest = pd.read_sql(query_latest, conn)

        query_first = f"SELECT video_id, daily_view_count FROM youtube_video WHERE keyword_id={keyword_id} AND update_count=1"
        df_first = pd.read_sql(query_first, conn)

        query_comments = f"SELECT video_id, analysis_id, like_count, is_ad FROM video_comment_analysis WHERE update_count={data_gradient}"
        df_comments = pd.read_sql(query_comments, conn)

    except Exception as e:
        print(f"오류-DB에 {keyword} 데이터를 가져오는 중 에러가 발생했습니다 : {e}")
        return {"conclusion": "DB 로드 중 에러 발생"}

    finally:
        conn.close()

    if df_comments.empty:
        comments_sum = pd.DataFrame(columns=['video_id', '댓글수', '댓글_좋아요_총합', '광고로_의심되는_댓글수'])

    else:
        comments_sum = df_comments.groupby("video_id").agg(
            댓글수=('analysis_id', 'count'),
            댓글_좋아요_총합=('like_count', 'sum'),
            광고로_의심되는_댓글수=('is_ad', 'sum')
        ).reset_index()

    df_Aoi = pd.merge(df_latest[['video_id', 'daily_view_count']],
                      df_first[['video_id', 'daily_view_count']],
                      on='video_id', suffixes=('_최신', '_초기'), how='left')
    # suffixes: 이름표를 추가로 붙이는 속성

    df_Aoi['daily_view_count_초기'] = df_Aoi['daily_view_count_초기'].fillna(0)
    df_Aoi['조회수 증가량'] = df_Aoi['daily_view_count_최신'] - df_Aoi['daily_view_count_초기']

    df_merged = pd.merge(df_latest, comments_sum, on='video_id', how='left')
    df_merged = pd.merge(df_merged, df_Aoi[['video_id', '조회수 증가량']], on='video_id', how='left')
    df_merged = df_merged.fillna(0)

    # 바이럴 점수 임시 계산식
    df_merged['바이럴 점수'] = (df_merged['조회수 증가량'] * 0.5) + \
                          (df_merged['댓글_좋아요_총합'] * 2) - \
                          (df_merged['광고로_의심되는_댓글수'] * 10)


    features = ['daily_view_count', 'daily_like_count', '댓글수', '댓글_좋아요_총합', '광고로_의심되는_댓글수', '조회수 증가량']
    x = df_merged[features]
    y = df_merged['바이럴 점수']

    if len(df_merged) < 2:
        print("오류-학습할 데이터의 개수가 너무 적습니다")
        return {"conclusion": "학습 데이터가 부족합니다."}

    X_train, X_test, Y_train, Y_test = train_test_split(x, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, Y_train)

    joblib.dump(model, f'rf_model_{keyword}.pkl')

    df_merged['예측 점수'] = model.predict(x)
    keyword_viral_score = df_merged['예측 점수'].mean()
    total_data_gradient = df_merged['조회수 증가량'].sum()
    total_suspect_ad = df_merged['광고로_의심되는_댓글수'].sum()

    viral_probability = max(0.0, min((keyword_viral_score / 6000.0) * 100, 100.0))

    results = {
        'keyword': keyword,
        'total_data_gradient': float(total_data_gradient),
        'total_suspect_ad': int(total_suspect_ad),
        'keyword_viral_score': float(keyword_viral_score),
        'viral_probability_percentage': f"{round(viral_probability, 1)}%",
        'conclusion': ""
    }

    if keyword_viral_score > 5000:
        results["conclusion"] = "인위적 바이럴 의심" if total_suspect_ad > 50 else "자연스러운 핫트렌드"
    elif keyword_viral_score > 1000:
        results["conclusion"] = "상승중인 트렌드"
    else:
        results["conclusion"] = "소강상태"

    return results

if __name__ == '__main__':
    viral_interpretation(DEFAULT_KEYWORD)