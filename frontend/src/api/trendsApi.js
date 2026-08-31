// 백엔드가 실제로 주는 실시간 데이터는 2개뿐입니다.
//   - 통합 × 급상승 -> GET /get_search_volume_ranking (네이버+구글 검색량 지수 합계)
//   - X   × 언급량  -> GET /get_mention_volume_ranking (X 트윗 언급 횟수)
// 나머지 조합(통합×언급량, 네이버 전체, 유튜브 전체, X×급상승)은
// 백엔드에 해당 API가 없어서 mock 데이터를 씁니다.
import { getSearchVolumeRanking, getMentionVolumeRanking } from "./rankingApi";

const MOCK_DATA = {
  all: {
    count: [
      { rank: 1, keyword: "마라탕", growth: "+180%", count: "320만" },
      { rank: 2, keyword: "두바이초콜릿", growth: "+245%", count: "280만" },
      { rank: 3, keyword: "요아정", growth: "+123%", count: "210만" },
    ],
  },
  naver: {
    growth: [{ rank: 1, keyword: "성수맛집", growth: "+310%", count: "87만" }],
    count: [{ rank: 1, keyword: "서울날씨", growth: "+30%", count: "510만" }],
  },
  youtube: {
    growth: [{ rank: 1, keyword: "쇼츠챌린지", growth: "+420%", count: "130만" }],
    count: [{ rank: 1, keyword: "먹방", growth: "+180%", count: "520만" }],
  },
  x: {
    growth: [{ rank: 1, keyword: "두바이초콜릿", growth: "+512%", count: "12.4만" }],
  },
};

const TOP_N = 10;

const mapSearchVolumeRanking = (rows) =>
  rows.slice(0, TOP_N).map((row, index) => ({
    rank: index + 1,
    keyword: row.target_keyword,
    growth: Number(row.total_relative_ratio).toFixed(1), // % 아님, 검색량 지수
    count: null,
  }));

const mapMentionVolumeRanking = (rows) =>
  rows.slice(0, TOP_N).map((row, index) => ({
    rank: index + 1,
    keyword: row.target_keyword,
    growth: null,
    count: row.mention_count,
  }));

// 이 조합이 실시간 데이터인지 여부 (부제목 표시용)
export const isLiveRanking = (platform, rankType) =>
  (platform === "all" && rankType === "growth") ||
  (platform === "x" && rankType === "count");

export const getTrendsData = async (platform, rankType) => {
  if (platform === "all" && rankType === "growth") {
    try {
      const res = await getSearchVolumeRanking();
      return mapSearchVolumeRanking(res.data || []);
    } catch (err) {
      console.error("검색량 순위 API 호출 실패:", err);
      return [];
    }
  }

  if (platform === "x" && rankType === "count") {
    try {
      const res = await getMentionVolumeRanking();
      return mapMentionVolumeRanking(res.data || []);
    } catch (err) {
      console.error("언급량 순위 API 호출 실패:", err);
      return [];
    }
  }

  const mockForPlatform = MOCK_DATA[platform] || {};
  return (mockForPlatform[rankType] || mockForPlatform.growth || []).slice(0, TOP_N);
};