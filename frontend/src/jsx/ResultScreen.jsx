import React from "react";
import "../css/ResultScreen.css";

const ResultScreen = ({ resultData, onReset }) => {
  // 백엔드에서 올 데이터 예시 (더미 데이터)
  const { keyword, isViral, score, reason, monthlyData } = resultData;

  return (
    <div className="result-page">
      <div className="background-glow"></div>

      <div className="result-container">
        <header className="result-header">
          <span className="analysis-tag">ANALYSIS COMPLETED</span>
          <h1>{keyword}</h1>
        </header>

        <div className="result-grid">
          {/* 1. 판별 카드 */}
          <div className="result-card verdict-card">
            <h3>판별 결과</h3>
            <div className={`verdict-badge ${isViral}`}>
              {isViral === "Viral"
                ? "🔥 자연 발생적 바이럴"
                : "📢 기업 주도형 마케팅"}
            </div>
            <p className="verdict-reason">{reason}</p>
          </div>

          {/* 2. 점수 카드 */}
          <div className="result-card score-card">
            <h3>바이럴 지수</h3>
            <div className="score-circle">
              <span className="score-number">{score}</span>
              <span className="score-unit">pt</span>
            </div>
          </div>

          {/* 3. 그래프 카드 (임시) */}
          <div className="result-card graph-card">
            <h3>월간 검색량 추이</h3>
            <div className="temp-graph">
              {/* 여기에 차후 Chart.js를 넣으면 졸업작품 퀄리티가 확 올라갑니다 */}
              <div className="graph-placeholder">Graph Visualization Area</div>
            </div>
          </div>
        </div>

        <button className="reset-btn" onClick={onReset}>
          다른 키워드 검색하기
        </button>
      </div>
    </div>
  );
};

export default ResultScreen;
