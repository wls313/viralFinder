import '../css/card.css';

function AIAnalysis({ result }) {

  if (!result) {
    return (
      <aside className="ai-panel">
        <div className="card">
          <h3>AI 분석 결과</h3>

          <div className="ai-result">
            <h2>분석 대기중</h2>

            <p>
              키워드를 분석하면 결과가 표시됩니다.
            </p>

            <div className="score-box">
              <span>바이럴 점수</span>
              <strong>-</strong>
            </div>
          </div>
        </div>
      </aside>
    );
  }

  // 업데이트 횟수가 부족한 경우
  if (typeof result.analysis === 'string') {
    return (
      <aside className="ai-panel">
        <div className="card">
          <h3>AI 분석 결과</h3>

          <div className="ai-result">
            <h2>데이터 수집중</h2>

            <p>{result.analysis}</p>

            <div className="score-box">
              <span>바이럴 점수</span>
              <strong>-</strong>
            </div>
          </div>
        </div>
      </aside>
    );
  }

  const analysis = result.analysis;

  const getResultInfo = () => {

    switch (analysis.conclusion) {

      case '인위적 바이럴 의심':
        return {
          title: '인위적 바이럴 의심',
          description: '광고성 확산 가능성이 높습니다.',
          color: '#ef4444'
        };

      case '상승중인 트렌드':
        return {
          title: '상승중인 트렌드',
          description: '관심도가 빠르게 증가하고 있습니다.',
          color: '#f59e0b'
        };

      case '자연스러운 핫트렌드':
        return {
          title: '자연스러운 핫트렌드',
          description: '자연스럽게 인기를 얻고 있는 키워드입니다.',
          color: '#22c55e'
        };

      default:
        return {
          title: '소강상태',
          description: '현재 큰 확산은 감지되지 않습니다.',
          color: '#64748b'
        };
    }
  };

  const info = getResultInfo();

  return (
    <aside className="ai-panel">
      <div className="card">

        <h3>AI 분석 결과</h3>

        <div className="ai-result">

          <h2 style={{ color: info.color }}>
            {info.title}
          </h2>

          <p>
            {info.description}
          </p>

          <div className="score-box">
            <span>바이럴 확률</span>

            <strong>
              {analysis.viral_probability_percentage}
            </strong>
          </div>

          <div className="score-box">
            <span>AI 점수</span>

            <strong>
              {analysis.keyword_viral_score.toFixed(2)}
            </strong>
          </div>

          <div className="score-box">
            <span>조회수 증가량</span>

            <strong>
              {analysis.total_data_gradient.toLocaleString()}
            </strong>
          </div>

          <div className="score-box">
            <span>광고 의심 댓글</span>

            <strong>
              {analysis.total_suspect_ad}
            </strong>
          </div>

        </div>

      </div>
    </aside>
  );
}

export default AIAnalysis;