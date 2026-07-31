import numpy as np
import pandas as pd
from google import genai
from google.genai import types
from server.config.config import GEMINI_API_KEY

def analyze_viral_traffic(trend_df, video_df):
    # 네이버 65% + 구글 35% 가중치 결합 (기존 유지)
    trend_df["interest_raw"] = (trend_df["weight_naver"] * 0.65) + (trend_df["weight_google"] * 0.35)

    trend_mean = trend_df["interest_raw"].mean()
    trend_std = trend_df["interest_raw"].std()
    if trend_std == 0 or pd.isna(trend_std):
        trend_std = 1.0

    trend_df["interest_z"] = (trend_df["interest_raw"] - trend_mean) / trend_std
    analysis_results = []

    # 조회수 정규화를 위한 기준값 설정 (영상이 비어있지 않다면 최댓값 기준으로 스케일링)
    max_view = video_df["view_count"].max() if not video_df.empty else 1.0
    if max_view == 0 or pd.isna(max_view):
        max_view = 1.0

    for _, video in video_df.iterrows():
        upload_date = video["uploaded_date"]
        upload_date_str = pd.to_datetime(video["uploaded_date"]).strftime('%Y-%m-%d')
        matched_trend = trend_df[trend_df["period"].astype(str) == upload_date_str]
        z_interest = matched_trend["interest_z"].values[0] if not matched_trend.empty else 0.0

        # 검색량 Z-Score를 시그모이드로 가공 (0 ~ 1 사이 안전벨트)
        sigmoid_val = 1 / (1 + np.exp(-z_interest))

        # 검색량은 낮은데 유튜브 조회수 비율이 비정상적으로 높으면 스코어가 치솟음
        # 0~100 스케일로 맞추기 위해 조회수 가중치 스코어링 도입
        view_ratio = (video["view_count"] / max_view) * 100
        denominator = 1.0 + 1.5 * sigmoid_val
        score = view_ratio / denominator

        analysis_results.append({
            "video_id": video["video_id"],
            "view_count": int(video["view_count"]),
            "z_interest": round(z_interest, 2),
            "score": round(score, 2),
            "status": "대기",
        })

    result_df = pd.DataFrame(analysis_results)
    if result_df.empty:
        return result_df

    q1 = result_df["score"].quantile(0.25)
    q3 = result_df["score"].quantile(0.75)
    iqr = q3 - q1

    warning_bound = q3 + (0.2 * iqr)
    suspect_bound = q3 + (0.6 * iqr)

    if suspect_bound > 60.0: suspect_bound = 60.0
    if warning_bound > 35.0: warning_bound = 35.0

    conditions = [
        (result_df["score"] > suspect_bound),
        (result_df["score"] > warning_bound) & (result_df["score"] <= suspect_bound),
        (result_df["score"] <= warning_bound),
        ]
    choices = ["바이럴 의심", "바이럴 주의", "정상"]
    result_df["status"] = np.select(conditions, choices, default="정상")

    return result_df[["video_id", "view_count", "z_interest", "score", "status"]]


def ask_gemini_evaluation(df_result_text, keyword_name):
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
    너는 디지털 마케팅 여론 분석가이자 소셜 트렌드 전문가야.
    아래 데이터셋은 키워드 '{keyword_name}'에 대한 대중 검색량(z_interest)과 유튜브 영상 트래픽 폭발도를 1차 통계 분석한 결과야.
    
    [1차 통계 분석 데이터]
    {df_result_text}
    
    🚨 [요구사항 - 핵심 뉴스 5개 엄선]
    1. 제공된 데이터에서 트렌드 지수(`z_interest`)가 변동하거나 급증한 시점을 파악해줘.
    2. 구글 검색 툴을 활용해서, 해당 시점에 '{keyword_name}'와 관련해 무슨 일이 있었는지 가장 신뢰도 높은 언론사(예: 네이버 뉴스, 대형 언론사)의 핵심 기사 딱 5개만 엄선해줘.
    3. 엄선한 5개의 기사만 리포트 하단에 아래 양식으로 '진짜 URL 주소'를 절대 변형하지 말고 그대로 출력해줘.
    - [기사 제목] (언론사명) : 실제 URL 주소
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig( # 💡 임포트 규격에 맞게 교정
                tools=[{"google_search": {}}],
                temperature=0.0
            )
        )

        ai_report = response.text
        metadata = response.candidates[0].grounding_metadata if response.candidates else None

        source_list = []
        if metadata and metadata.grounding_chunks:
            seen_urls = set()
            for chunk in metadata.grounding_chunks:
                if len(source_list) >= 5:
                    break
                if chunk.web and chunk.web.uri:
                    uri = chunk.web.uri
                    if uri not in seen_urls and ("news" in uri or "naver" in uri or "co.kr" in uri):
                        source_list.append({
                            "title": chunk.web.title if chunk.web.title else "관련 보도 자료",
                            "url": uri
                        })
                        seen_urls.add(uri)

        return {
            "summary": ai_report,
            "verification_sources": source_list
        }

    except Exception as e:
        return {"summary": f"❌ 제미나이 연동 에러 발생: {e}", "verification_sources": []}