import pandas as pd

def analyze_viral_traffic(trend_df: pd.DataFrame, video_df: pd.DataFrame = None):
    if trend_df.empty:
        return {
            "latest_naver_ratio": 0.0,
            "latest_google_ratio": 0.0,
            "raw_data_preview": []
        }

    naver_col = "naver_ratio" if "naver_ratio" in trend_df.columns else "weight_naver"
    google_col = "google_ratio" if "google_ratio" in trend_df.columns else "weight_google"
    period_col = "period" if "period" in trend_df.columns else "measurement_date"

    if pd.api.types.is_datetime64_any_dtype(trend_df[period_col]):
        trend_df[period_col] = trend_df[period_col].dt.strftime("%Y-%m-%d")

    preview_df = trend_df[[period_col, naver_col, google_col]].tail(10).copy()
    preview_records = preview_df.rename(columns={
        period_col: "period",
        naver_col: "naver",
        google_col: "google"
    }).to_dict(orient="records")

    latest_row = trend_df.iloc[-1]
    latest_naver = float(latest_row.get(naver_col, 0.0))
    latest_google = float(latest_row.get(google_col, 0.0))

    return {
        "latest_naver_ratio": round(latest_naver, 2),
        "latest_google_ratio": round(latest_google, 2),
        "raw_data_preview": preview_records
    }