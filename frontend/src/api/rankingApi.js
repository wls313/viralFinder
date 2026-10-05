import axios from "axios";
 
// 랭킹 API(statistical_ranking_dispenser.py)는 /search와는 별도의 FastAPI
// 앱으로 실행됩니다. 8001번 포트에서 실행 중이어야 합니다.
const RANKING_API_URL = "http://localhost:8001";
 
// 검색량 순위 (네이버+구글 상대 검색량 합계, 최근 1개월)
// -> {status, message, count, data: [{keyword_id, target_keyword, total_relative_ratio}]}
export const getSearchVolumeRanking = async (keyword) => {
  const response = await axios.get(`${RANKING_API_URL}/get_search_volume_ranking`);
  return response.data;
};
 
// 언급량 순위 (X 트윗 언급 횟수, 최근 1개월)
// -> {status, message, count, data: [{keyword_id, target_keyword, mention_count}]}
export const getMentionVolumeRanking = async (keyword) => {
  const response = await axios.get(`${RANKING_API_URL}/get_mention_volume_ranking`);
  return response.data;
};
 
// 조회수 최고 유튜브 영상 (국내 인기 급상승 영상)
// -> {status, count, data: [{type: "youtube", url, full_text, created_at}]}
export const getRecommendedVideo = async (keyword) => {
  const response = await axios.get(`${RANKING_API_URL}/get_recommended_video`, {params: {keyword}});
  return response.data;
};
 
// 조회수 최고 X(트위터) 게시물
// -> {status, count, data: [{type: "tweet", url, full_text, created_at}]}
export const getRecommendedTweet = async (keyword) => {
  const response = await axios.get(`${RANKING_API_URL}/get_recommended_tweet`, {params: {keyword}});
  return response.data;
};
 