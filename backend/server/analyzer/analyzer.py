import pandas as pd

SHORT_WINDOW_DAYS = 3
LONG_WINDOW_DAYS = 14
MIN_DAYS_FOR_TREND = 7
UP_THRESHOLD = 1.05
DOWN_THRESHOLD = 0.95


def _clean_series(df: pd.DataFrame, value_col: str) -> pd.Series:
    if value_col not in df.columns or df.empty:
        return pd.Series(dtype=float)
    d = df.sort_values("created_at") if "created_at" in df.columns else df
    d = d.drop_duplicates(subset="period", keep="last")
    return d.set_index("period")[value_col].sort_index()


def _windowed_avg(series: pd.Series, days: int, as_of):
    if series.empty:
        return None, 0
    start = as_of - pd.Timedelta(days=days - 1)
    window = series[(series.index >= start) & (series.index <= as_of)]
    if window.empty:
        return None, 0
    return float(window.mean()), window.index.nunique()


def _momentum(series: pd.Series, as_of):
    short_avg, _ = _windowed_avg(series, SHORT_WINDOW_DAYS, as_of)
    long_avg, long_days = _windowed_avg(series, LONG_WINDOW_DAYS, as_of)

    if short_avg is None or long_days < MIN_DAYS_FOR_TREND:
        return {
            "short_term_avg": round(short_avg, 1) if short_avg else 0.0,
            "long_term_avg": round(long_avg, 1) if long_avg else 0.0,
            "prediction": "INSUFFICIENT_DATA",
        }

    if short_avg > long_avg * UP_THRESHOLD:
        prediction = "UP"
    elif short_avg < long_avg * DOWN_THRESHOLD:
        prediction = "DOWN"
    else:
        prediction = "STAY"

    return {
        "short_term_avg": round(short_avg, 1),
        "long_term_avg": round(long_avg, 1),
        "prediction": prediction,
    }


def analyze_viral_traffic(trend_df: pd.DataFrame):
    if trend_df is None or trend_df.empty:
        empty = {"short_term_avg": 0.0, "long_term_avg": 0.0, "prediction": "INSUFFICIENT_DATA"}
        return {
            "latest_naver_ratio": 0.0,
            "latest_google_ratio": 0.0,
            "naver": empty,
            "google": empty,
            "math_prediction": "INSUFFICIENT_DATA",
        }

    naver_series = _clean_series(trend_df, "weight_naver")
    google_series = _clean_series(trend_df, "weight_google")
    as_of = trend_df["period"].max()

    naver_result = _momentum(naver_series, as_of)
    google_result = _momentum(google_series, as_of)

    preds = [r["prediction"] for r in (naver_result, google_result) if r["prediction"] != "INSUFFICIENT_DATA"]
    if not preds:
        math_prediction = "INSUFFICIENT_DATA"
    elif len(set(preds)) == 1:
        math_prediction = preds[0]
    else:
        math_prediction = "STAY"

    return {
        "latest_naver_ratio": float(naver_series.iloc[-1]) if not naver_series.empty else 0.0,
        "latest_google_ratio": float(google_series.iloc[-1]) if not google_series.empty else 0.0,
        "naver": naver_result,
        "google": google_result,
        "math_prediction": math_prediction,
    }
