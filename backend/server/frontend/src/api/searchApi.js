import axios from "axios";

const API_URL = "http://localhost:8000";

export const searchKeyword = async (keyword, period = "90") => {

    const validPeriods = ["7", "30", "90"];
    const safePeriod = validPeriods.includes(String(period)) ? String(period) : "90";

    const response = await axios.get(
      `${API_URL}/api/analysis/${encodeURIComponent(keyword)}`,
      {
          params: {period: safePeriod}
      }
  );
  console.log("트렌드 데이터 받음:", response.data);

  return response.data;
};