import axios from "axios";

const API_URL = "http://localhost:8000";

export const searchKeyword = async (keyword, period = "1w") => {
  // period: "1w" | "1m" | "3m"
  // 백엔드 /search가 아직 period 파라미터를 사용하지 않음(현재는 7일 고정).
  // 백엔드에서 지원되면 이 값을 그대로 활용하면 됨.
  const response = await axios.post(
    `${API_URL}/search`,
    {
      keyword,
      period,
    }
  );
  console.log(response.data);

  return response.data;
};