import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split

def viral_interpretation(keyword):
    print("\n바이럴 판독 시작")
    video_csv = f'videos_{keyword}.csv'
    comments_csv = f'comments_{keyword}.csv'

    try:
        df_videos = pd.read_csv(video_csv)
        df_comments = pd.read_csv(comments_csv)
    except FileNotFoundError:
        print(f"{keyword}의 CSV 파일이 존재하지 않습니다.")
        return

    comments_sum = df_comments.groupby("영상id").agg(
        댓글수=('댓글 번호', 'count'),
        댓글_좋아요_총합=('좋아요', 'sum'),
        광고로_의심되는_댓글수=('광고여부', 'sum')
    ).reset_index()

    data_gradient = df_videos['업데이트 횟수'].max()
    df_latest = df_videos[df_videos['업데이트 횟수'] == data_gradient]
    df_first = df_videos[df_videos['업데이트 횟수'] == 1]

    df_Aoi = pd.merge(df_latest[['영상id', '일일 조회수']],
                      df_first[['영상id', '일일 조회수']],
                      on='영상id', suffixes=('_최신', '_초기'), how='left')
    # suffixes: 이름표를 추가로 붙이는 속성

    df_Aoi['일일 조회수_초기'] = df_Aoi['일일 조회수_초기'].fillna(0)
    df_Aoi['조회수 증가량'] = df_Aoi['일일 조회수_최신'] - df_Aoi['일일 조회수_초기']

    df_merged = pd.merge(df_latest, comments_sum, on='영상id', how='left')
    df_merged = pd.merge(df_merged, df_Aoi[['영상id', '조회수 증가량']], on='영상id', how='left')
    df_merged = df_merged.fillna(0)

    # 바이럴 점수 임시 계산식
    df_merged['바이럴 점수'] = (df_merged['조회수 증가량'] * 0.5) + \
                          (df_merged['댓글_좋아요_총합'] * 2) - \
                          (df_merged['광고로_의심되는_댓글수'] * 10)


    features = ['일일 조회수', '일일 좋아요수', '댓글수', '댓글_좋아요_총합', '광고로_의심되는_댓글수', '조회수 증가량']
    x = df_merged[features]
    y = df_merged['바이럴 점수']

    if len(df_merged) < 2:
        print("오류-학습할 데이터의 개수가 너무 적습니다")
        return

    X_train, X_test, Y_train, Y_test = train_test_split(x, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, Y_train)

    joblib.dump(model, f'rf_model_{keyword}.pkl')

    df_merged['예측 점수'] = model.predict(x)
    keyword_viral_score = df_merged['예측 점수'].mean()
    total_data_gradient = df_merged['조회수 증가량'].sum()
    total_suspect_ad = df_merged['광고로_의심되는_댓글수'].sum()

    results = {
        'keyword': keyword,
        'total_data_gradient': float(total_data_gradient),
        'total_suspect_ad': int(total_suspect_ad),
        'keyword_viral_score': float(keyword_viral_score),
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
    viral_interpretation('dummy')