import axios from "axios";

const API_URL = "http://localhost:8000";

export const searchKeyword = async (keyword, period = "1w") => {

    const periodMap = {
        "1w": "7",
        "1m": "30",
        "3m": "90"
    };
    const mappingPeriod = periodMap[period] || "7"

    const response = await axios.get(
      `${API_URL}/api/analysis/${encodeURIComponent(keyword)}`,
      {
          params: {period: mappingPeriod}
      }
  );
  console.log("트렌드 데이터 받음:", response.data);

  return response.data;
};