import "../css/dashboard.css";

function ComparePage() {
  return (
    <section>
      <div className="page-header">
        <h1>비교 분석</h1>

        <p>두 키워드의 바이럴 정도를 비교합니다.</p>
      </div>

      <div className="compare-layout">
        <div className="card compare-card">
          <h3>버터쿠키</h3>

          <div className="score viral">바이럴 81%</div>
        </div>

        <div className="vs-text">VS</div>

        <div className="card compare-card">
          <h3>마라탕</h3>

          <div className="score marketing">광고 62%</div>
        </div>
      </div>
    </section>
  );
}

export default ComparePage;
