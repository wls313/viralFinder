import axios from "axios";

const API_BASE_URL = "http://localhost:8001";

export async function getTrendsData(platform, rankType, period=7) {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/rankings?period=${period}`);
    const allData = response.data.data;

    let targetData = [];
    if (platform === "all" && rankType === "growth") targetData = allData.integrated_surge;
    if (platform === "all" && rankType === "count") targetData = allData.integrated_mention;
    if (platform === "naver" && rankType === "growth") targetData = allData.naver_surge;
    if (platform === "naver" && rankType === "count") targetData = allData.naver_mention;
    if (platform === "google" && rankType === "growth") targetData = allData.google_surge;
    if (platform === "google" && rankType === "count") targetData = allData.google_mention;

    const formattedData = targetData.map((item, index) => {
      return {
        rank: index + 1,
        keyword: item.target_keyword,
        score: item.score,
        growth: item.delta !== null ? parseFloat(item.delta).toFixed(1) : null,
        count: item.mention_count || 0
      };
    });

    return formattedData;
  } catch (error) {
    console.error("랭킹 데이터를 불러오는데 실패했습니다:", error);
    return [];
  }
}

export function isLiveRanking(platform, rankType) {
  return true;
}