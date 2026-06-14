import { useState, useEffect } from "react";
import { getTrendsData } from "../api/trendsApi";
import "../css/trends.css";

function TrendsPage() {
  const [platform, setPlatform] = useState("all");
  const [rankType, setRankType] = useState("growth");
  const [favorites, setFavorites] = useState([]);
  const [data, setData] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      const result = await getTrendsData(platform, rankType);
      setData(result);
    };
    fetchData();
  }, [platform, rankType]);

  const toggleFavorite = (keyword) => {
    setFavorites(prev => 
      prev.includes(keyword) 
        ? prev.filter(item => item !== keyword) 
        : [...prev, keyword]
    );
  };

  return (
    <div className="trends-page">
      <div className="section-header">
        <div>
          <h2>실시간 트렌드</h2>
          <p>네이버 · 유튜브 기반 실시간 인기 키워드 (더미데이터)</p>
        </div>
        <div className="top-tabs">
          {["all", "naver", "youtube"].map((p) => (
            <button key={p} className={platform === p ? "active" : ""} onClick={() => setPlatform(p)}>
              {p === "all" ? "통합" : p === "naver" ? "네이버" : "유튜브"}
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
          <table>
            <thead>
              <tr>
                <th style={{ width: "80px" }}>순위</th>
                <th style={{ width: "auto" }}>키워드</th>
                <th style={{ width: "150px" }}>상승률</th>
                <th style={{ width: "150px" }}>언급량</th>
                <th style={{ width: "90px" }}>관심</th>
              </tr>
            </thead>
            <tbody>
              {data.map((item) => (
                <tr key={item.keyword}>
                  <td><span className="rank-badge">{item.rank}</span></td>
                  <td className="keyword-cell">{item.keyword}</td>
                  <td className="up">▲ {item.growth}</td>
                  <td>{item.count}</td>
                  <td>
                    <button className="favorite-btn" onClick={() => toggleFavorite(item.keyword)}>
                      <span className={favorites.includes(item.keyword) ? "favorite-active" : "favorite-inactive"}>♥</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
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