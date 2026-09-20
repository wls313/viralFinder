import { useEffect, useState } from "react";
import "../css/LoadingPage.css";

// 기존에는 진행률(%)을 프론트에서 임의로 애니메이션했는데, 실제로는 97%에서
// 백엔드 응답을 기다리며 오래 멈춰있는 것처럼 보이는 문제가 있었습니다
// (퍼센트가 실제 진행 상황과 무관했기 때문). 정확한 퍼센트를 보장할 수 없는
// 상황이라, 오해를 주는 숫자 대신 "지금 무엇을 하고 있는지"를 보여주는
// 스피너 + 단계 문구로 대체했습니다.
const STAGES = [
  "오늘 업로드된 영상을 탐색하는 중",
  "조회수 · 좋아요 데이터를 수집하는 중",
  "네이버 · 구글 트렌드 데이터를 확인하는 중",
  "바이럴 여부를 분석하는 중",
];

const STAGE_INTERVAL_MS = 2800;

function LoadingPage() {
  const [stageIndex, setStageIndex] = useState(0);
  const [dots, setDots] = useState("");

  // 단계 문구를 순환시켜서 "계속 진행 중"이라는 걸 보여줌
  // (실제 백엔드 단계와 1:1로 정확히 맞진 않지만, 오래 걸리는 구간에서도
  // 화면이 멈춰있다는 느낌을 주지 않기 위함)
  useEffect(() => {
    const timer = setInterval(() => {
      setStageIndex((prev) => (prev + 1) % STAGES.length);
    }, STAGE_INTERVAL_MS);

    return () => clearInterval(timer);
  }, []);

  // 점 애니메이션
  useEffect(() => {
    const dotTimer = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? "" : prev + "."));
    }, 500);

    return () => clearInterval(dotTimer);
  }, []);

  return (
    <div className="container">
      {/* 로고 */}
      <h1 className="logo">Trend Tracker</h1>

      {/* 스피너 */}
      <div className="spinner" aria-hidden="true">
        <div className="spinner-ring" />
        <span className="spinner-icon">📈</span>
      </div>

      {/* 문구 */}
      <p className="loading-text">
        {STAGES[stageIndex]}
        {dots}
      </p>

      <p className="loading-subtext">
        데이터 양에 따라 시간이 조금 더 걸릴 수 있어요
      </p>
    </div>
  );
}

export default LoadingPage;
