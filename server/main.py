import logging
import json
from database import fetch_data
from analyzer import analyze_viral_traffic, ask_gemini_evaluation

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main(keyword_input):
    try:
        trend_df, video_df, keyword_id = fetch_data(keyword_input)

        if keyword_id is None or trend_df.empty or video_df.empty:
            logging.warning(f"키워드 '{keyword_input}': 데이터가 부족합니다.")
            return

        result_df = analyze_viral_traffic(trend_df, video_df)

        df_text = result_df.to_string(index=False)
        ai_report_dict = ask_gemini_evaluation(df_text, keyword_input)

        statistical_analysis = result_df.to_dict(orient="records")

        final_api_response = {
            "status": "success",
            "keyword_id": keyword_id,
            "keyword_name": keyword_input,
            "statistics": statistical_analysis,
            "ai_evaluation": ai_report_dict
        }
        print("\n🚀 [API 서버 응답 시뮬레이션 - 최종 전송용 JSON]")
        print("========================================================")
        print(json.dumps(final_api_response, ensure_ascii=False, indent=4))
        print("========================================================")

    except Exception as e:
        logging.error(f"분석 파이프라인 가동 중 실패: {e}")

if __name__ == "__main__":
    user_input = input("👉 분석할 키워드명 또는 ID를 입력하세요: ").strip()
    if user_input:
        main(user_input)