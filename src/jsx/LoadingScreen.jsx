import React, { useState, useEffect } from "react";
import "../css/LoadingScreen.css";

const LoadingScreen = ({ keyword, onFinished }) => {
  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState("데이터 수집 엔진 가동 중...");

  useEffect(() => {
    // 1. 프로그레스 바 애니메이션 로직
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setTimeout(onFinished, 500); // 100% 도달 후 결과 화면으로 이동
          return 100;
        }
        return prev + 1; // 1씩 증가 (속도 조절 가능)
      });
    }, 40); // 약 4초 동안 진행

    // 2. 진행도에 따른 상태 메시지 변경
    if (progress < 30) setStatusText(`'${keyword}' 관련 게시글 수집 중...`);
    else if (progress < 60)
      setStatusText("커뮤니티 언급량 및 조회수 분석 중...");
    else if (progress < 90) setStatusText("바이럴 신뢰도 알고리즘 연산 중...");
    else setStatusText("최종 분석 리포트 생성 중...");

    return () => clearInterval(interval);
  }, [progress, keyword, onFinished]);

  return (
    <div className="loading-page">
      <div className="tech-bg-overlay"></div>

      <div className="loading-container">
        <h1 className="loading-logo">ViralFinder</h1>

        <div className="loading-box">
          <div className="status-header">
            <span className="status-label">ANALYZING</span>
            <span className="percentage">{progress}%</span>
          </div>

          <div className="progress-track">
            <div className="progress-bar" style={{ width: `${progress}%` }}>
              <div className="bar-glow"></div>
            </div>
          </div>

          <div className="status-footer">
            <p className="status-text">{statusText}</p>
            <div className="scanner-line"></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoadingScreen;
