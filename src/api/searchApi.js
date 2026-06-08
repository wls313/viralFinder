import axios from "axios";

const BASE_URL = "http://localhost:8000";

export async function searchKeyword(keyword) {
  const response = await axios.post(`${BASE_URL}/search`, {
    keyword,
  });

  return response.data;
}
