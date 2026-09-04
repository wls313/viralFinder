import '../css/dashboard.css';

const FALLBACK_KEYWORDS = ['버터쿠키', '두바이초콜릿', '마라탕'];

// topKeywords: 실시간 트렌드 1~3위 (App.jsx에서 trendsApi 기반으로 전달됨).
// 아직 안 불러와졌거나 비어있으면 기본 키워드로 대체.
function EmptyState({ setKeyword, topKeywords }) {
  const keywords =
    topKeywords && topKeywords.length > 0
      ? topKeywords
      : FALLBACK_KEYWORDS;

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
          {keywords.map((word) => (
            <button key={word} onClick={() => setKeyword(word)}>
              {word}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}

export default EmptyState;
