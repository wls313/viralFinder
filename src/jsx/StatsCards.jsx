import '../css/card.css';

function StatsCards() {
  return (
    <div className="stats-grid">
      <div className="card">
        <p>총 언급량</p>
        <h3>28,541</h3>
      </div>

      <div className="card">
        <p>바이럴 점수</p>
        <h3>81%</h3>
      </div>

      <div className="card">
        <p>광고 점수</p>
        <h3>19%</h3>
      </div>
    </div>
  );
}

export default StatsCards;