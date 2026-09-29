import axios from "axios";

const AI_API_URL = "http://localhost:8080";

export const getGraphComment = async ({ keyword, period = "1w" }) => {
  const response = await axios.get(`${AI_API_URL}/api/trends/recommend`, {
    params: { keyword, period },
    timeout: 180000,
  });
  return response.data;
};