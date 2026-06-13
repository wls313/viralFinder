import axios from "axios";

const API_URL = "http://localhost:8000";

export const searchKeyword = async (keyword) => {
  const response = await axios.post(
    `${API_URL}/search`,
    {
      keyword,
    }
  );
  console.log(response.data);

  return response.data;
};