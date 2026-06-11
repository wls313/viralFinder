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

  const getResultInfo = () => {
    switch (result.status) {
      case '바이럴 의심':
        return {
          title: '바이럴 의심',

          description:
            '비정상적인 확산 패턴이 감지되었습니다.',

          color: '#ef4444',
        };

      case '바이럴 주의':
        return {
          title: '바이럴 주의',

          description:
            '일부 마케팅성 확산 가능성이 있습니다.',

          color: '#f59e0b',
        };

      default:
        return {
          title: '정상',

          description:
            '자연스러운 사용자 반응 기반 확산입니다.',

          color: '#22c55e',
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

          <p>{info.description}</p>

          <div className="score-box">
            <span>바이럴 점수</span>

            <strong>
              {result.score}
            </strong>
          </div>
        </div>
      </div>
    </aside>
  );
}

export default AIAnalysis;