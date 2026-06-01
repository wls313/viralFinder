import { useEffect, useState } from "react";
import "../css/LoadingPage.css";

function LoadingPage() {

  const [progress, setProgress] = useState(0);
  const [dots, setDots] = useState("");

  // 로딩 퍼센트 증가
  useEffect(() => {

    const timer = setInterval(() => {

      setProgress((prev) => {

        if (prev >= 100) {
          clearInterval(timer);
          return 100;
        }

        return prev + 1;

      });

    }, 50);

    return () => clearInterval(timer);

  }, []);

  // 점 애니메이션
  useEffect(() => {

    const dotTimer = setInterval(() => {

      setDots((prev) => {

        if (prev.length >= 3) {
          return "";
        }

        return prev + ".";
      });

    }, 500);

    return () => clearInterval(dotTimer);

  }, []);

  // 상황별 문구
  const getLoadingMessage = () => {

    if (progress <= 30) {
      return "데이터 수집 중";
    }

    if (progress <= 70) {
      return "패턴 분석 중";
    }

    return "결과 생성 중";
  };

  return (
    <div className="container">

      {/* 로고 */}
      <h1 className="logo">
        ViralFinder
      </h1>

      {/* 로딩바 */}
      <div className="bar-background">

        <div
          className="bar-fill"
          style={{ width: `${progress}%` }}
        ></div>

      </div>

      {/* 퍼센트 */}
      <p className="percent">
        {progress}%
      </p>

      {/* 문구 */}
      <p className="loading-text">
        {getLoadingMessage()}{dots}
      </p>

    </div>
  );
}

export default LoadingPage;