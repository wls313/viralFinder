import re
from google import genai
from google.genai import types

from key_setting import gemini_api_key

client = genai.Client(api_key=gemini_api_key)

# 광고 검사 설정
commercial_keyword = ["유료광고포함", "파트너스", "협찬", "AD", "commercial"]
commercial_pattern = [
    re.compile(r'(소정의|일정액의)\s*(원고료|수수료|대가).*(받|제공|지급)'),
    re.compile(r'(제품|기기|서비스).*(무상|무료|협찬).*(제공|지원|대여)'),
    re.compile(r'(파트너스|커넥트|어필리에이트).*(활동|일환|수익|링크)'),
    re.compile(r'(링크).*(클릭|확인)')
]

# 연관성 체크
def AD_search(text, keyword):
    text = str(text).strip()
    keyword = str(keyword).strip()
    if not text:
        return 0

    # 1단계. 키워드 검사
    if any(word in text for word in commercial_keyword):
        return 1
    if any(pattern.search(text) for pattern  in commercial_pattern):
        return 1

    instruction = f"""
            너는 유튜브 스팸 및 광고, 연관성 없는 댓글을 필터링해야 해. 아래 두 가지 중 조건에 맞는 하나로 대답해.

            1. 1: 문맥상 '{keyword}'와 무관하거나, 광고/스팸으로 추정되는 댓글인 경우
            2. 0: 문맥상 '{keyword}'와 관련있는 자연스러운 반응 혹은 일상적인 댓글인 경우
            오직 "1" 또는 "0" 중 하나의 단어로만 대답해. 다른 말을 절대로 덧붙이지 마!
        """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=text,
            config=types.GenerateContentConfig(
                system_instruction=instruction,
                temperature=0.1 # 대답에 대한 창의성
            )
        )
        result = response.text.strip()

        if result == '1':
            return 1
        else:
            return 0

    except Exception as e:
        print(f"오류-gemini API로 댓글을 판독하는 중 에러 발생 : {e}")
        return 0;

