import os, sys
import time
import json
import random
import re
import concurrent.futures

from google import genai

# 상위(server) 폴더 경로
current_dir = os.path.dirname(os.path.realpath(__file__))
top_level_dir = os.path.dirname(current_dir)
if top_level_dir not in sys.path:
    sys.path.append(top_level_dir)

from server.key_setting import gemini_api_key

client = genai.Client(api_key=gemini_api_key)

# 광고 검사 설정
commercial_keyword = ["유료광고포함", "파트너스", "협찬", "AD", "commercial", '공산당']
commercial_pattern = [
    re.compile(r'(소정의|일정액의)\s*(원고료|수수료|대가).*(받|제공|지급)'),
    re.compile(r'(제품|기기|서비스).*(무상|무료|협찬).*(제공|지원|대여)'),
    re.compile(r'(파트너스|커넥트|어필리에이트).*(활동|일환|수익|링크)'),
    re.compile(r'(링크).*(클릭|확인)')
]

def gemini_process(batch_comments_list, keyword, max_retries=3):
    if not batch_comments_list:
        return []

    inst = f"""
            {len(batch_comments_list)}개의 댓글에서 아래 중 맞는 값 하나로 대답해라

            1: 도박, 불법 사이트 링크 유도, 의미 없는 문자열 반복, 어뷰징, '{keyword}'와 전혀 무관한 뜬금없는 홍보성 댓글
            0: 문맥상 '{keyword}'와 관련있는 반응 혹은 {keyword}와 관련된 일반적인 댓글인 경우
            오직 "1" 또는 "0" 중 하나의 단어로만 대답해. 다른 말을 절대로 덧붙이지 마!
        """

    for i, text in enumerate(batch_comments_list):
        inst += f"[{i + 1}] {text}\n"

    inst += """
            출력 형식은 반드시 0과 1로만 구성된 JSON 배열 리스트 형태의 텍스트만 출력해(예: [0, 1, 0, 0, 1])
            설명이나 마크다운 백틱(```)은 절대 넣지마. 배열만 출력시켜.
        """

    # API 호출 랜덤 딜레이
    time.sleep(random.uniform(0.5, 2.0))

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=inst
            )
            res_text = response.text.strip()

            res_text = re.sub(r'```json|```', '', res_text).strip()

            ad_results = json.loads(res_text)

            if len(ad_results) != len(batch_comments_list):
                raise ValueError(f"오류-길이 불일치! (요청: {len(batch_comments_list)}, 응답: {len(ad_results)})")

            return ad_results

        except Exception as e:
            msg = str(e).lower()
            if 'quota' in msg or 'exhausted' in msg:
                print("API의 일일 무료 할당량을 모두 소진했습니다. 해당 배치를 0으로 처리합니다")
                return [0] * len(batch_comments_list)

            if "429" in msg:
                print(f"API의 RPM을 초과했습니다. 60초간 대기합니다... : ({attempt + 1}/{max_retries})")
                time.sleep(60)

            else:
                wait_time = (2 ** attempt) * 2 + random.uniform(0, 1)
                print(f"gemini API 지연 발생! {wait_time:.1f}초 대기 후 재시도합니다... : ({attempt + 1}/{max_retries})")
                time.sleep(wait_time)

    print("최대 재시도 횟수를 초과하여 해당 배치를 0으로 처리합니다.")
    return [0] * len(batch_comments_list)

# 연관성 체크
def AD_search(comments_list, keyword, batch_size=100, max_workers=2, max_retries=5):
    if not comments_list:
        return []

    pre_filtered_results = [0] * len(comments_list)
    ask_comments_no_space = []
    gemini_indices = []

    for i, text in enumerate(comments_list):
        is_obvious_ad = False

        if any(kw in text for kw in commercial_keyword):
            is_obvious_ad = True

        if not is_obvious_ad:
            for pattern in commercial_pattern:
                if pattern.search(text):
                    is_obvious_ad = True
                    break

        if is_obvious_ad:
            pre_filtered_results[i] = 1
        else:
            text_no_space = re.sub(r'\s+', '', text)
            ask_comments_no_space.append(text_no_space)
            gemini_indices.append(i)

    if not ask_comments_no_space:
        return pre_filtered_results

    batches = []
    indices_batches = []
    for i in range(0, len(ask_comments_no_space), batch_size):
        batches.append(ask_comments_no_space[i:i + batch_size])
        indices_batches.append(gemini_indices[i:i + batch_size])

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(gemini_process, batch, keyword, max_retries):
                idx_batch
            for batch, idx_batch in zip(batches, indices_batches)
        }

        for future in concurrent.futures.as_completed(futures):
            idx_batch = futures[future]
            try:
                batch_result = future.result()
                for idx, res in zip(idx_batch, batch_result):
                    pre_filtered_results[idx] = res
            except Exception as exc:
                print(f"오류-배치 스레드 처리 중 예외 처리가 발생했습니다! : {exc}")

    return pre_filtered_results