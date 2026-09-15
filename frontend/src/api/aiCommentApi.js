import axios from "axios";

// Spring AI 백엔드 (가정) - 별도 서버/포트에서 실행된다고 가정
const AI_API_URL = "http://localhost:8080";

export const getGraphComment = async ({ keyword, naverTrend, googleTrend, xTrend }) => {
  const response = await axios.post(`${AI_API_URL}/api/ai/graph-comment`, {
    keyword,
    naverTrend,
    googleTrend,
    xTrend,
  });

  return response.data; // { comment, probability }
};