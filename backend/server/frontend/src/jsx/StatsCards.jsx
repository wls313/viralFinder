import '../css/card.css';

function StatsCards({ result }) {

  const analysis = result?.analysis;

  if (!analysis || typeof analysis === 'string') {
    return null;
  }

  return (
    <div className="stats-grid">

      <div className="card">
        <p>조회수 증가량</p>
        <h3>
          {analysis.total_data_gradient.toLocaleString()}
        </h3>
      </div>

      <div className="card">
        <p>바이럴 점수</p>
        <h3>
          {analysis.keyword_viral_score.toFixed(2)}
        </h3>
      </div>

      <div className="card">
        <p>광고 의심 댓글</p>
        <h3>
          {analysis.total_suspect_ad}
        </h3>
      </div>

    </div>
  );
}

export default StatsCards;