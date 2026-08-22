import pandas as pd

def analyze_viral_traffic(trend_df: pd.DataFrame):
    if trend_df is None or trend_df.empty:
        return None

    latest_naver = trend_df['naver_ratio'].iloc[-1] if 'naver_ratio' in trend_df.columns else 0
    latest_google = trend_df['google_ratio'].iloc[-1] if 'google_ratio' in trend_df.columns else 0

    short_term_avg = 0.0
    long_term_avg = 0.0
    math_prediction = "STAY"

    if 'naver_ratio' in trend_df.columns and len(trend_df) >= 3:
        short_term_avg = trend_df['naver_ratio'].tail(3).mean()

        tail_count = 14 if len(trend_df) >= 14 else len(trend_df)
        long_term_avg = trend_df['naver_ratio'].tail(tail_count).mean()

        if short_term_avg > (long_term_avg * 1.05):
            math_prediction = "UP"
        elif short_term_avg < (long_term_avg * 0.95):
            math_prediction = "DOWN"

    return {
        "latest_naver_ratio": float(latest_naver),
        "latest_google_ratio": float(latest_google),
        "short_term_avg": round(float(short_term_avg), 1),
        "long_term_avg": round(float(long_term_avg), 1),
        "math_prediction": math_prediction
    }