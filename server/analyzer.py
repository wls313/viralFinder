from google.genai import types
from google import genai
from config import GEMINI_API_KEY
import numpy as np
import pandas as pd

def analyze_viral_traffic(trend_df, video_df):
    trend_df["interest_raw"] = (trend_df["weight_naver"] * 0.65) + (trend_df["weight_google"] * 0.35)

    trend_mean = trend_df["interest_raw"].mean()
    trend_std = trend_df["interest_raw"].std()
    if trend_std == 0 or pd.isna(trend_std):
        trend_std = 1.0

    trend_df["interest_z"] = (trend_df["interest_raw"] - trend_mean) / trend_std
    analysis_results = []

    for _, video in video_df.iterrows():
        upload_date = video["uploaded_date"]
        matched_trend = trend_df[trend_df["period"] == upload_date]

        z_interest = matched_trend["interest_z"].values[0] if not matched_trend.empty else 0.0
        sigmoid_val = 1 / (1 + np.exp(-z_interest))
        denominator = 1.0 + 4.0 * sigmoid_val
        score = video["positive_ratio"] / denominator

        analysis_results.append({
            "video_id": video["video_id"],
            "title": video["caption_name"],
            "positive_ratio": video["positive_ratio"],
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

    return result_df[["video_id", "title", "positive_ratio", "z_interest", "score", "status"]]


def ask_gemini_evaluation(df_result_text, keyword_name):

    client = genai.Client(api_key=GEMINI_API_KEY)

    # 💡 [핵심] 제미나이가 구글에 검색할 때 무조건 뉴스 기사를 긁어오도록 유도하는 강제 프롬프트
    prompt = f"""
    너는 디지털 마케팅 여론 분석가이자 소셜 트렌드 전문가야.
    아래 데이터셋은 키워드 '{keyword_name}'에 대한 포털 검색량(z_interest)과 유튜브 영상 여론을 1차 통계 분석한 결과야.
    
    [1차 통계 분석 데이터]
    {df_result_text}
    
    🚨 [요구사항 - 핵심 뉴스 5개 엄선]
    1. 구글 검색 툴을 사용하여 2026년 4월 30일 전후로 발생한 '{keyword_name}' 관련 연예인 초청 행사, 포토콜, 또는 대중 매체 노출 사건을 검증해줘.
    2. 무분별한 링크를 다 가져오지 말고, 검색 결과 중 가장 신뢰도 높은 언론사(예: 네이버 뉴스, 대형 신문사 및 방송사)의 핵심 기사 딱 5개만 엄선해줘.
    3. 엄선한 5개의 기사만 리포트 하단에 아래 양식으로 '진짜 URL 주소'를 절대 변형하지 말고 그대로 출력해줘.
    - [기사 제목] (언론사명) : 실제 URL 주소

    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                tools=[{"google_search": {}}],
                temperature=0.0  # 창의성 차단 (출처 데이터 확보 최적화)
            )
        )

        ai_report = response.text
        metadata = response.candidates[0].grounding_metadata if response.candidates else None

        source_list = []
        if metadata and metadata.grounding_chunks:
            seen_urls = set()
            for chunk in metadata.grounding_chunks:
                if len(source_list) >= 5:  # 딱 5개만 제한
                    break
                if chunk.web and chunk.web.uri:
                    uri = chunk.web.uri
                    # 중복 제거 및 주요 도메인 필터링
                    if uri not in seen_urls and ("news" in uri or "naver" in uri or "co.kr" in uri):
                        source_list.append({
                            "title": chunk.web.title if chunk.web.title else "관련 보도 자료",
                            "url": uri
                        })
                        seen_urls.add(uri)

        # 🎁 텍스트 문자열 대신 프론트 맞춤형 딕셔너리로 최종 리턴
        return {
            "summary": ai_report,
            "verification_sources": source_list
        }

    except Exception as e:
        return f"❌ 제미나이 연동 에러 발생: {e}"