// src/api/trendsApi.js
//
// TODO(백엔드): 아직 실시간 트렌드 API가 없습니다. 아래 MOCK_DATA를 사용 중이며,
// 실제 엔드포인트가 준비되면 getTrendsData()의 구현부만 교체하면 됩니다.
//
// 기대하는 API 계약 (예시):
//   GET /trends?platform=all|naver|youtube&rankType=growth|count
//   -> [{ rank, keyword, growth, count }, ...]  (최대 10개, rank 오름차순)

const MOCK_DATA = {
  all: {
    growth: [
      { rank: 1, keyword: "두바이초콜릿", growth: "+245%", count: "128만" },
      { rank: 2, keyword: "마라탕", growth: "+180%", count: "95만" },
      { rank: 3, keyword: "버터쿠키", growth: "+145%", count: "74만" },
      { rank: 4, keyword: "요아정", growth: "+123%", count: "63만" },
      { rank: 5, keyword: "먹태깡", growth: "+98%", count: "51만" },
      { rank: 6, keyword: "탕후루", growth: "+87%", count: "47만" },
      { rank: 7, keyword: "크루키", growth: "+76%", count: "42만" },
      { rank: 8, keyword: "약과", growth: "+65%", count: "38만" },
      { rank: 9, keyword: "인생네컷", growth: "+54%", count: "33만" },
      { rank: 10, keyword: "스탠리컵", growth: "+48%", count: "29만" },
    ],
    count: [
      { rank: 1, keyword: "마라탕", growth: "+180%", count: "320만" },
      { rank: 2, keyword: "두바이초콜릿", growth: "+245%", count: "280만" },
      { rank: 3, keyword: "요아정", growth: "+123%", count: "210만" },
      { rank: 4, keyword: "버터쿠키", growth: "+145%", count: "180만" },
      { rank: 5, keyword: "먹태깡", growth: "+98%", count: "150만" },
      { rank: 6, keyword: "탕후루", growth: "+87%", count: "132만" },
      { rank: 7, keyword: "크루키", growth: "+76%", count: "115만" },
      { rank: 8, keyword: "약과", growth: "+65%", count: "98만" },
      { rank: 9, keyword: "인생네컷", growth: "+54%", count: "81만" },
      { rank: 10, keyword: "스탠리컵", growth: "+48%", count: "70만" },
    ],
  },
  naver: {
    growth: [
      { rank: 1, keyword: "성수맛집", growth: "+310%", count: "87만" },
      { rank: 2, keyword: "한강축제", growth: "+280%", count: "72만" },
      { rank: 3, keyword: "서울데이트", growth: "+190%", count: "64만" },
      { rank: 4, keyword: "성수카페", growth: "+160%", count: "55만" },
      { rank: 5, keyword: "홍대맛집", growth: "+120%", count: "48만" },
      { rank: 6, keyword: "제주여행", growth: "+110%", count: "44만" },
      { rank: 7, keyword: "부산맛집", growth: "+95%", count: "39만" },
      { rank: 8, keyword: "캠핑용품", growth: "+82%", count: "34만" },
      { rank: 9, keyword: "홈트레이닝", growth: "+70%", count: "30만" },
      { rank: 10, keyword: "반려동물용품", growth: "+61%", count: "27만" },
    ],
    count: [
      { rank: 1, keyword: "서울날씨", growth: "+30%", count: "510만" },
      { rank: 2, keyword: "한강공원", growth: "+55%", count: "430만" },
      { rank: 3, keyword: "성수카페", growth: "+120%", count: "310만" },
      { rank: 4, keyword: "홍대맛집", growth: "+80%", count: "290만" },
      { rank: 5, keyword: "서울데이트", growth: "+60%", count: "250만" },
      { rank: 6, keyword: "제주여행", growth: "+110%", count: "220만" },
      { rank: 7, keyword: "부산맛집", growth: "+95%", count: "198만" },
      { rank: 8, keyword: "캠핑용품", growth: "+82%", count: "170만" },
      { rank: 9, keyword: "홈트레이닝", growth: "+70%", count: "150만" },
      { rank: 10, keyword: "반려동물용품", growth: "+61%", count: "132만" },
    ],
  },
  youtube: {
    growth: [
      { rank: 1, keyword: "쇼츠챌린지", growth: "+420%", count: "130만" },
      { rank: 2, keyword: "브이로그", growth: "+250%", count: "101만" },
      { rank: 3, keyword: "먹방", growth: "+180%", count: "82만" },
      { rank: 4, keyword: "ASMR", growth: "+150%", count: "75만" },
      { rank: 5, keyword: "게임실황", growth: "+120%", count: "68만" },
      { rank: 6, keyword: "여행브이로그", growth: "+105%", count: "60만" },
      { rank: 7, keyword: "챌린지", growth: "+92%", count: "53만" },
      { rank: 8, keyword: "커버댄스", growth: "+80%", count: "47만" },
      { rank: 9, keyword: "리뷰영상", growth: "+68%", count: "41만" },
      { rank: 10, keyword: "언박싱", growth: "+55%", count: "36만" },
    ],
    count: [
      { rank: 1, keyword: "먹방", growth: "+180%", count: "520만" },
      { rank: 2, keyword: "쇼츠챌린지", growth: "+420%", count: "470만" },
      { rank: 3, keyword: "브이로그", growth: "+250%", count: "350만" },
      { rank: 4, keyword: "ASMR", growth: "+150%", count: "300만" },
      { rank: 5, keyword: "게임실황", growth: "+120%", count: "260만" },
      { rank: 6, keyword: "여행브이로그", growth: "+105%", count: "230만" },
      { rank: 7, keyword: "챌린지", growth: "+92%", count: "205만" },
      { rank: 8, keyword: "커버댄스", growth: "+80%", count: "180만" },
      { rank: 9, keyword: "리뷰영상", growth: "+68%", count: "158만" },
      { rank: 10, keyword: "언박싱", growth: "+55%", count: "140만" },
    ],
  },
};

const TOP_N = 10;

export const getTrendsData = async (platform, rankType) => {
  // 나중에 여기서 fetch(API_URL)을 사용하세요.
  return MOCK_DATA[platform][rankType].slice(0, TOP_N);
};
