import '../css/dashboard.css';

function EmptyState({ setKeyword }) {
  return (
    <section className="empty-state">
      <div className="empty-box">
        <h2>
          키워드를 검색해서
          바이럴 여부를 분석해보세요
        </h2>

        <p>
          SNS, 블로그, 검색 데이터를 기반으로
          광고/자연 바이럴 여부를 분석합니다.
        </p>

        <div className="keyword-list">
          <button onClick={() => setKeyword('버터쿠키')}>
            버터쿠키
          </button>

          <button onClick={() => setKeyword('두바이초콜릿')}>
            두바이초콜릿
          </button>

          <button onClick={() => setKeyword('마라탕')}>
            마라탕
          </button>
        </div>
      </div>
    </section>
  );
}

export default EmptyState;