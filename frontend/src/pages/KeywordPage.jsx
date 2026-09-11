import "../css/dashboard.css";

function KeywordPage() {
  const keywords = ["버터쿠키", "두바이초콜릿", "마라탕", "탕후루", "크루키"];

  return (
    <section>
      <div className="page-header">
        <h1>키워드 분석</h1>

        <p>최근 많이 분석된 키워드입니다.</p>
      </div>

      <div className="keyword-grid">
        {keywords.map((item) => (
          <div className="card" key={item}>
            <h3>{item}</h3>

            <p>실시간 바이럴 분석 가능</p>

            <button className="analyze-small-btn">분석하기</button>
          </div>
        ))}
      </div>
    </section>
  );
}

export default KeywordPage;
