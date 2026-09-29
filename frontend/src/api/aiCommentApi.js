import axios from "axios";

const AI_API_URL = "http://localhost:8080";

// 같은 검색 결과에 대한 AI 코멘트 요청은 한 번만 보낸다.
// - React StrictMode(개발 모드)가 effect를 두 번 실행해도 요청이 중복되지 않고
// - 다른 메뉴에 갔다가 돌아와 컴포넌트가 다시 만들어져도 재요청(=Spring이 파이썬 재크롤링)하지 않는다.
// 실패한 요청은 캐시에서 제거해서 "다시 시도"가 실제로 재요청되게 한다.
const requestCache = new Map();

export const getGraphComment = ({ keyword, period = "90", cacheKey }) => {
  const key = cacheKey || `${keyword}|${period}`;

  if (requestCache.has(key)) {
    return requestCache.get(key);
  }

  const promise = axios
    .get(`${AI_API_URL}/api/trends/recommend`, {
      params: { keyword, period },
      // Spring이 파이썬 크롤링(최대 약 3분) + Gemini 호출까지 기다리므로 넉넉하게 설정
      timeout: 300000,
    })
    .then((response) => response.data)
    .catch((error) => {
      requestCache.delete(key);
      throw error;
    });

  requestCache.set(key, promise);
  return promise;
};
