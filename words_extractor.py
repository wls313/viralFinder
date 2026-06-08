import time
import json
import re
from google import genai
from google.genai import types

from key_setting import gemini_api_key

client = genai.Client(api_key=gemini_api_key)

# 광고 검사 설정
commercial_keyword = ["유료광고포함", "파트너스", "협찬", "AD", "commercial", '공산당']
commercial_pattern = [
    re.compile(r'(소정의|일정액의)\s*(원고료|수수료|대가).*(받|제공|지급)'),
    re.compile(r'(제품|기기|서비스).*(무상|무료|협찬).*(제공|지원|대여)'),
    re.compile(r'(파트너스|커넥트|어필리에이트).*(활동|일환|수익|링크)'),
    re.compile(r'(링크).*(클릭|확인)')
]

# 연관성 체크
def AD_search(comments_list, keyword):
    if not comments_list:
        return []

    pre_filtered_results = []
    ask_comments = []
    gemini_indices = []

    for i, text in enumerate(comments_list):
        is_ovbious_ad = False

        if any(kw in text for kw in commercial_keyword):
            is_ovbious_ad = True

        if not is_ovbious_ad:
            for pattern in commercial_pattern:
                if pattern.search(text):
                    is_ovbious_ad = True
                    break

        if is_ovbious_ad:
            pre_filtered_results.append(1)
        else:
            pre_filtered_results.append(0)
            ask_comments.append(text)
            gemini_indices.append(i)

    if not ask_comments:
        return pre_filtered_results

    instruction = f"""
            너는 {len(ask_comments)}개의 댓글 건에 맞는 하나로 대답해.

            1. 1: 도박, 불법 사이트 링크 유도, 의미 없는 문자열 반복, 어뷰징, '{keyword}'와 전혀 무관한 뜬금없는 홍보성 댓글
            2. 0: 문맥상 '{keyword}'와 관련있는 반응 혹은 {keyword}와 관련된 일반적인 댓글인 경우
            오직 "1" 또는 "0" 중 하나의 단어로만 대답해. 다른 말을 절대로 덧붙이지 마!
        """

    for i, text in enumerate(comments_list):
        instruction += f"[{i+1}] {text}\n"

    instruction += """
        출력 형식은 반드시 0과 1로만 구성된 JSON 배열 리스트 형태의 텍스트만 출력해(예: [0, 1, 0, 0, 1])
        설명이나 마크다운 백틱(```)은 절대 넣지마. 배열만 출력시켜.
    """

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=instruction
            )
            res_text = response.text.strip()

            res_text = re.sub(r'```json|```', '', res_text).strip()

            ad_results = json.loads(res_text)

            if len(ad_results) != len(ask_comments):
                print(f"경고-반환된 결과 개수가 달라 다시 시도합니다...")
                raise ValueError("오류-길이 불일치!")

            for idx, gemini_result in zip(gemini_indices, ad_results):
                pre_filtered_results[idx] = gemini_result

            return pre_filtered_results

        except Exception as e:
            print(f"gemini API 지연 발생! 5초 대기 후 재시도합니다... : ({attempt+1}/{max_retries})")
            time.sleep(5)

    return pre_filtered_results