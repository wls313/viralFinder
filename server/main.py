import logging
from database import fetch_data
from analyzer import analyze_viral_traffic, ask_gemini_evaluation

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main(keyword_input):
    try:
        # 1. DB에서 데이터 로드 (문자열 또는 ID 입력 처리)
        trend_df, video_df, keyword_id = fetch_data(keyword_input)

        if keyword_id is None:
            print(f"❌ 에러: '{keyword_input}'는 DB에 등록되지 않은 키워드명입니다.")
            return

        if trend_df.empty or video_df.empty:
            logging.warning(f"키워드 '{keyword_input}' (ID: {keyword_id}): 분석할 시계열 데이터가 부족합니다.")
            return

        # 2. 정량적 통계 분석 실행
        result_df = analyze_viral_traffic(trend_df, video_df)

        print(f"\n========================================================")
        print(f" 📊 [1단계] 정량적 통계 기반 스코어링 표 (키워드: {keyword_input})")
        print(f"========================================================")
        print(result_df.to_string(index=False))
        print(f"========================================================")

        # 3. 제미나이 AI 정성 리포트 실행
        df_text = result_df.to_string(index=False)
        print(f"\n🤖 [2단계] Gemini AI 지능형 종합 평가 리포트")
        print(f"========================================================")
        ai_report = ask_gemini_evaluation(df_text, keyword_input)
        print(ai_report)
        print(f"========================================================")

    except Exception as e:
        logging.error(f"분석 파이프라인 가동 중 실패: {e}")

if __name__ == "__main__":
    print("========================================================")
    print("        🔍 Viral Finder 분석 시스템 가동")
    print("========================================================")

    user_input = input("👉 분석할 키워드명 또는 ID를 입력하세요: ").strip()

    if user_input:
        main(user_input)
    else:
        print("❌ 에러: 키워드를 입력해 주세요.")