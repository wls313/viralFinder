import os
import sys
import json
import logging
import subprocess

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_ROOT = os.path.dirname(CURRENT_DIR)

# X 크롤링 모듈 로드
try:
    from server.crawling.apify_x_crawling import search_x
except ImportError:
    sys.path.append(os.path.join(SERVER_ROOT, "crawling"))
    from apify_x_crawling import search_x


def run_sequential_crawling(keyword: str) -> dict:
    naver_data = []
    google_data = []

    # 1. 네이버 데이터랩 크롤링
    logging.info(f"[1/3] 네이버 수집 시작: {keyword}")
    try:
        naver_script = os.path.join(SERVER_ROOT, "crawling", "naver_data_lab_crawling.py")
        result = subprocess.run(
            [sys.executable, naver_script, keyword],
            capture_output=True,
            text=True,
            encoding='utf-8',
            cwd=SERVER_ROOT,
            timeout=60
        )
        if result.returncode == 0 and result.stdout.strip():
            output_data = json.loads(result.stdout.strip())
            if output_data.get("status") == "success":
                naver_data = output_data.get("data", [])
                logging.info("[1/3] 네이버 수집 완료")
    except Exception as e:
        logging.error(f"[1/3] 네이버 수집 실패 (스킵 후 다음 진행): {e}")

    # 2. 구글 트렌드 크롤링
    logging.info(f"[2/3] 구글 수집 시작: {keyword}")
    try:
        google_script = os.path.join(SERVER_ROOT, "crawling", "pytrends_crawling.py")
        result = subprocess.run(
            [sys.executable, google_script, keyword],
            capture_output=True,
            text=True,
            encoding='utf-8',
            cwd=SERVER_ROOT,
            timeout=120
        )
        if result.returncode == 0 and result.stdout.strip():
            output_data = json.loads(result.stdout.strip())
            if output_data.get("status") == "success":
                google_data = output_data.get("data", [])
                logging.info("[2/3] 구글 수집 완료")
    except Exception as e:
        logging.error(f"[2/3] 구글 수집 실패 (스킵 후 다음 진행): {e}")

    # 3. X (Twitter) 크롤링
    logging.info(f"[3/3] X(Twitter) 수집 시작: {keyword}")
    x_tweets = []
    try:
        raw_res = search_x(keyword)

        if isinstance(raw_res, list):
            x_tweets = raw_res
        elif isinstance(raw_res, dict):
            x_tweets = raw_res.get("x_trends_data", raw_res.get("data", raw_res.get("tweets", [])))
        else:
            x_tweets = []

        logging.info(f"[3/3] X(Twitter) 수집 완료 ({len(x_tweets)}건)")
    except Exception as e:
        logging.error(f"[3/3] X(Twitter) 수집 실패: {e}")
        x_tweets = []

    return {
        "naver_data": naver_data,
        "google_data": google_data,
        "x_trends_data": x_tweets
    }