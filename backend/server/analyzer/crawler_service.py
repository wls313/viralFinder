import os
import sys
import logging
import subprocess

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_ROOT = os.path.dirname(CURRENT_DIR)

# X 크롤링 모듈 로드
try:
    from crawling.x_data_abstraction import get_X_data
except ImportError:
    sys.path.append(os.path.join(SERVER_ROOT, "crawling"))
    from x_data_abstraction import get_X_data


def run_sequential_crawling(keyword: str) -> list:
    """
    네이버 -> 구글 -> X(Twitter) 순서로 크롤링을 진행합니다.
    하나가 실패해도 다음 크롤러가 정상 작동하도록 개별 예외처리를 적용했습니다.
    """
    # 1. 네이버 데이터랩 크롤링
    logging.info(f"[1/3] 네이버 수집 시작: {keyword}")
    try:
        naver_script = os.path.join(SERVER_ROOT, "crawling", "naver_data_lab_crawling.py")
        subprocess.run(
            [sys.executable, naver_script, keyword],
            text=True,
            encoding='utf-8',
            cwd=SERVER_ROOT,
            timeout=60
        )
        logging.info("[1/3] 네이버 수집 완료")
    except Exception as e:
        logging.error(f"[1/3] 네이버 수집 실패 (스킵 후 다음 진행): {e}")

    # 2. 구글 트렌드 크롤링
    logging.info(f"[2/3] 구글 수집 시작: {keyword}")
    try:
        google_script = os.path.join(SERVER_ROOT, "crawling", "pytrends_crawling.py")
        subprocess.run(
            [sys.executable, google_script, keyword],
            text=True,
            encoding='utf-8',
            cwd=SERVER_ROOT,
            timeout=120
        )
        logging.info("[2/3] 구글 수집 완료")
    except Exception as e:
        logging.error(f"[2/3] 구글 수집 실패 (스킵 후 다음 진행): {e}")

    # 3. X (Twitter) 크롤링
    logging.info(f"[3/3] X(Twitter) 수집 시작: {keyword}")
    x_tweets = []
    try:
        x_tweets = get_X_data(keyword, max_items=5)
        logging.info(f"[3/3] X(Twitter) 수집 완료 ({len(x_tweets)}건)")
    except Exception as e:
        logging.error(f"[3/3] X(Twitter) 수집 실패: {e}")

    return x_tweets