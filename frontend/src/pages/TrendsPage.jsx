import "../css/dashboard.css";

function TrendsPage() {
  const trends = [
    {
      rank: 1,
      keyword: "버터쿠키",
      score: "+245%",
    },
    {
      rank: 2,
      keyword: "두바이초콜릿",
      score: "+181%",
    },
    {
      rank: 3,
      keyword: "크루키",
      score: "+143%",
    },
  ];

  return (
    <section>
      <div className="page-header">
        <h1>실시간 트렌드</h1>

        <p>현재 급상승 중인 키워드입니다.</p>
      </div>

      <div className="trend-list">
        {trends.map((item) => (
          <div className="card trend-item" key={item.rank}>
            <div>
              <h2>#{item.rank}</h2>
            </div>

            <div className="trend-info">
              <h3>{item.keyword}</h3>
              <p>언급량 급증</p>
            </div>

            <div className="trend-score">{item.score}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

export default TrendsPage;
