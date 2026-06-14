import { useEffect, useState } from "react";
import "../css/LoadingPage.css";
import { getProgress } from "../api/progressApi";


function LoadingPage() {
  console.log("LoadingPage 렌더링");
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState("분석 준비 중");
  const [dots, setDots] = useState("");

  // 로딩 퍼센트 증가
  useEffect(() => {

    const timer = setInterval(async () => {

      try {

        const data = await getProgress();
        console.log(data);
        setProgress(data.percent);
        setMessage(data.message);

      } catch (err) {

        console.error(err);

      }

    }, 500);

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



  const getStep = () => {

    if (progress <= 20) return "1 / 5";
    if (progress <= 40) return "2 / 5";
    if (progress <= 60) return "3 / 5";
    if (progress <= 85) return "4 / 5";

    return "5 / 5";
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

      <p className="step">
        {getStep()} 단계
      </p>

      {/* 문구 */}
      <p className="loading-text">
        {message}{dots}
      </p>

    </div>
  );
}

export default LoadingPage;