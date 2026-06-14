// src/api/trendsApi.js

const MOCK_DATA = {
  all: {
    growth: [
      { rank: 1, keyword: "두바이초콜릿", growth: "+245%", count: "128만" },
      { rank: 2, keyword: "마라탕", growth: "+180%", count: "95만" },
      { rank: 3, keyword: "버터쿠키", growth: "+145%", count: "74만" },
      { rank: 4, keyword: "요아정", growth: "+123%", count: "63만" },
      { rank: 5, keyword: "먹태깡", growth: "+98%", count: "51만" },
    ],
    count: [
      { rank: 1, keyword: "마라탕", growth: "+180%", count: "320만" },
      { rank: 2, keyword: "두바이초콜릿", growth: "+245%", count: "280만" },
      { rank: 3, keyword: "요아정", growth: "+123%", count: "210만" },
      { rank: 4, keyword: "버터쿠키", growth: "+145%", count: "180만" },
      { rank: 5, keyword: "먹태깡", growth: "+98%", count: "150만" },
    ],
  },
  naver: {
    growth: [
      { rank: 1, keyword: "성수맛집", growth: "+310%", count: "87만" },
      { rank: 2, keyword: "한강축제", growth: "+280%", count: "72만" },
      { rank: 3, keyword: "서울데이트", growth: "+190%", count: "64만" },
      { rank: 4, keyword: "성수카페", growth: "+160%", count: "55만" },
      { rank: 5, keyword: "홍대맛집", growth: "+120%", count: "48만" },
    ],
    count: [
      { rank: 1, keyword: "서울날씨", growth: "+30%", count: "510만" },
      { rank: 2, keyword: "한강공원", growth: "+55%", count: "430만" },
      { rank: 3, keyword: "성수카페", growth: "+120%", count: "310만" },
      { rank: 4, keyword: "홍대맛집", growth: "+80%", count: "290만" },
      { rank: 5, keyword: "서울데이트", growth: "+60%", count: "250만" },
    ],
  },
  youtube: {
    growth: [
      { rank: 1, keyword: "쇼츠챌린지", growth: "+420%", count: "130만" },
      { rank: 2, keyword: "브이로그", growth: "+250%", count: "101만" },
      { rank: 3, keyword: "먹방", growth: "+180%", count: "82만" },
      { rank: 4, keyword: "ASMR", growth: "+150%", count: "75만" },
      { rank: 5, keyword: "게임실황", growth: "+120%", count: "68만" },
    ],
    count: [
      { rank: 1, keyword: "먹방", growth: "+180%", count: "520만" },
      { rank: 2, keyword: "쇼츠챌린지", growth: "+420%", count: "470만" },
      { rank: 3, keyword: "브이로그", growth: "+250%", count: "350만" },
      { rank: 4, keyword: "ASMR", growth: "+150%", count: "300만" },
      { rank: 5, keyword: "게임실황", growth: "+120%", count: "260만" },
    ],
  },
};

export const getTrendsData = async (platform, rankType) => {
  // 나중에 여기서 fetch(API_URL)을 사용하세요.
  return MOCK_DATA[platform][rankType];
};