import logging
import subprocess
import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_ROOT = os.path.dirname(CURRENT_DIR)

if SERVER_ROOT not in sys.path:
    sys.path.append(SERVER_ROOT)

from server.config.database import fetch_data
from server.analyzer.analyzer import analyze_viral_traffic, ask_gemini_evaluation

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def run_crawling(keyword):

    logging.info(f"네이버 크롤링 시작")
    naver_path = os.path.join(SERVER_ROOT,"crawling", "naver_data_lab_crawling.py")
    subprocess.run([sys.executable, naver_path, keyword], text=True, encoding='utf-8', cwd=SERVER_ROOT)
    logging.info(f"구글 크롤링 시작")
    google_path = os.path.join(SERVER_ROOT,"crawling", "pytrends_crawling.py")
    subprocess.run([sys.executable, google_path, keyword], text=True, encoding='utf-8', cwd=SERVER_ROOT)

    logging.info(f"유튜브 크롤링 시작")
    youtube_path = os.path.join(SERVER_ROOT,"crawling", "new_youtube_data_abstraction.py")
    subprocess.run([sys.executable, youtube_path, keyword], text=True, encoding='utf-8', cwd=SERVER_ROOT)

def main(keyword):
    try:
        run_crawling(keyword)

        trend_df, video_df, keyword_id = fetch_data(keyword)

        if keyword_id is None or trend_df.empty or video_df.empty:
            logging.warning(f"키워드 '{keyword}'에 대한 데이터가 존재하지않습니다.")
            return

        result_df = analyze_viral_traffic(trend_df, video_df)

        df_text = result_df.to_string(index=False)
        ai_report_dict = ask_gemini_evaluation(df_text, keyword)

        statistical_analysis = result_df.to_dict(orient="records")

        final_api_response = {
            "status": "success",
            "keyword_id": keyword_id,
            "keyword_name": keyword,
            "statistics": statistical_analysis,
            "ai_evaluation": ai_report_dict
        }

        return final_api_response

    except Exception as e:
        logging.error(f"분석 파이프라인 가동 중 실패: {e}")

if __name__ == "__main__":
    user_input = input("분석할 키워드를 입력하세요: ").strip()
    if user_input:
        main(user_input)
