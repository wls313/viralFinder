import { useEffect, useRef, useState } from "react";
import "../css/LoadingPage.css";
import { getProgress } from "../api/progressApi";

// 댓글 크롤링 단계가 제거되면서 파이프라인이 짧아짐(영상 검색 → 통계 수집 → 바이럴 분석).
// 백엔드 /progress는 아직 실제 percent/message를 갱신하지 않아서(항상 0%),
// 백엔드 값이 들어오면 그걸 우선 반영하고, 없으면 프론트에서 단계별로 자연스럽게
// 채워지는 애니메이션으로 대체합니다.
const STEPS = [
  { until: 40, message: "오늘 업로드된 영상을 탐색하는 중" },
  { until: 80, message: "조회수 · 좋아요 데이터를 수집하는 중" },
  { until: 97, message: "바이럴 여부를 분석하는 중" },
];

function LoadingPage() {
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState(STEPS[0].message);
  const [dots, setDots] = useState("");
  const backendProgressRef = useRef(0);

  // 백엔드 진행률 폴링 (연결되면 자연스럽게 우선 반영, 없으면 무시)
  useEffect(() => {
    const timer = setInterval(async () => {
      try {
        const data = await getProgress();
        if (typeof data?.percent === "number") {
          backendProgressRef.current = data.percent;
        }
      } catch (err) {
        // 백엔드 진행률 API가 없거나 실패해도 아래 클라이언트 애니메이션으로 계속 진행
      }
    }, 500);

    return () => clearInterval(timer);
  }, []);

  // 클라이언트 측 진행 애니메이션 (실제 소요 시간이 짧아진 파이프라인 기준)
  useEffect(() => {
    const tick = setInterval(() => {
      setProgress((prev) => {
        const target = Math.max(backendProgressRef.current, 97);
        const next = prev + Math.max(1, (target - prev) * 0.08);
        return Math.min(next, target);
      });
    }, 150);

    return () => clearInterval(tick);
  }, []);

  // 진행률에 맞춰 단계 문구 갱신
  useEffect(() => {
    const step = STEPS.find((s) => progress <= s.until) || STEPS[STEPS.length - 1];
    setMessage(step.message);
  }, [progress]);

  // 점 애니메이션
  useEffect(() => {
    const dotTimer = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? "" : prev + "."));
    }, 500);

    return () => clearInterval(dotTimer);
  }, []);

  const displayPercent = Math.round(progress);
  const currentStepIndex = STEPS.findIndex((s) => progress <= s.until);
  const stepNumber = currentStepIndex === -1 ? STEPS.length : currentStepIndex + 1;

  return (
    <div className="container">
      {/* 로고 */}
      <h1 className="logo">Trend Tracker</h1>

      {/* 로딩바 */}
      <div className="bar-background">
        <div className="bar-fill" style={{ width: `${displayPercent}%` }}></div>
      </div>

      {/* 퍼센트 */}
      <p className="percent">{displayPercent}%</p>

      <p className="step">{stepNumber} / {STEPS.length} 단계</p>

      {/* 문구 */}
      <p className="loading-text">
        {message}
        {dots}
      </p>
    </div>
  );
}

export default LoadingPage;