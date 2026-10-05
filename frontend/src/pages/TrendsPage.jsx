import { useState, useEffect } from "react";
import { getTrendsData, isLiveRanking } from "../api/trendsApi";
import "../css/trends.css";

const PLATFORM_LABEL = { all: "통합", naver: "네이버", youtube: "유튜브", x: "X" };

function TrendsPage() {
  const [platform, setPlatform] = useState("all");
  const [rankType, setRankType] = useState("growth");
  const [favorites, setFavorites] = useState([]);
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let ignore = false;
    setLoading(true);
    getTrendsData(platform, rankType).then((result) => {
      if (!ignore) {
        setData(result);
        setLoading(false);
      }
    });
    return () => { ignore = true; };
  }, [platform, rankType]);

  const toggleFavorite = (keyword) => {
    setFavorites(prev =>
      prev.includes(keyword)
        ? prev.filter(item => item !== keyword)
        : [...prev, keyword]
    );
  };

  const live = isLiveRanking(platform, rankType);

  return (
    <div className="trends-page">
      <div className="section-header">
        <div>
          <h2>실시간 트렌드</h2>
          <p>{live ? "네이버 · 구글 · X 기반 실시간 랭킹" : "인기 키워드 (예시 데이터, 백엔드 연동 전)"}</p>
        </div>
        <div className="top-tabs">
          {["all", "naver", "youtube", "x"].map((p) => (
            <button key={p} className={platform === p ? "active" : ""} onClick={() => setPlatform(p)}>
              {PLATFORM_LABEL[p]}
            </button>
          ))}
        </div>
      </div>

      <div className="content">
        <div className="main-panel">
          <div className="rank-tabs">
            <button className={rankType === "growth" ? "active" : ""} onClick={() => setRankType("growth")}>급상승 순위</button>
            <button className={rankType === "count" ? "active" : ""} onClick={() => setRankType("count")}>언급량 순위</button>
          </div>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th style={{ width: "80px" }}>순위</th>
                  <th style={{ width: "auto" }}>키워드</th>
                  <th style={{ width: "150px" }}>{rankType === "growth" ? "검색량 지수" : "상승률"}</th>
                  <th style={{ width: "150px" }}>언급량</th>
                  <th style={{ width: "90px" }}>관심</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={5} className="table-empty">불러오는 중...</td></tr>
                ) : data.length === 0 ? (
                  <tr><td colSpan={5} className="table-empty">표시할 데이터가 없습니다.</td></tr>
                ) : (
                  data.map((item) => (
                    <tr key={item.keyword}>
                      <td><span className="rank-badge">{item.rank}</span></td>
                      <td className="keyword-cell">{item.keyword}</td>
                      <td className="up">{item.growth != null ? `▲ ${item.growth}` : "-"}</td>
                      <td>{item.count != null ? item.count : "-"}</td>
                      <td>
                        <button className="favorite-btn" onClick={() => toggleFavorite(item.keyword)}>
                          <span className={favorites.includes(item.keyword) ? "favorite-active" : "favorite-inactive"}>♥</span>
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
        <div className="side-panel">
          <h3>관심 키워드</h3>
          {favorites.length === 0 ? (
            <div className="empty-favorite">관심 키워드를 추가해보세요</div>
          ) : (
            favorites.map((keyword) => (
              <div className="favorite-item" key={keyword}>
                <span>{keyword}</span>
                <button className="favorite-remove-btn" onClick={() => toggleFavorite(keyword)}>♥</button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

export default TrendsPage;