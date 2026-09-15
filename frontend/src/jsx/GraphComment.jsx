import { useEffect, useState } from "react";
import { getGraphComment } from "../api/aiCommentApi";
import "../css/graphComment.css";

const PROBABILITY_INFO = {
  HIGH: { label: "상승 확률 높음", color: "#22c55e" },
  MEDIUM: { label: "상승 확률 보통", color: "#f59e0b" },
  LOW: { label: "상승 확률 낮음", color: "#ef4444" },
};

// 백엔드(Spring AI) 미기동/실패 시 보여줄 예시 데이터
const DUMMY_COMMENT = {
  comment: "최근 3주간 검색량이 꾸준히 우상향하고 있어 추가 상승 여지가 있어 보입니다.",
  probability: "MEDIUM",
};

function GraphComment({ keyword, result }) {
  const [comment, setComment] = useState(null);
  const [probability, setProbability] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isDummy, setIsDummy] = useState(false);

  useEffect(() => {
    let ignore = false;

    const hasTrendData =
      result?.naver_trend?.length || result?.google_trend?.length || result?.x_trend?.length;

    if (!hasTrendData) {
      // 검색 전 상태에서도 예시 데이터를 보여줌 (TopContent와 동일한 정책)
      setComment(DUMMY_COMMENT.comment);
      setProbability(DUMMY_COMMENT.probability);
      setIsDummy(true);
      setLoading(false);
      return;
    }

    (async () => {
      setLoading(true);

      try {
        const data = await getGraphComment({
          keyword,
          naverTrend: (result.naver_trend || []).map((item) => ({
            period: item.period,
            ratio: item.relative_ratio,
          })),
          googleTrend: (result.google_trend || []).map((item) => ({
            period: item.period,
            ratio: item.relative_ratio,
          })),
          xTrend: (result.x_trend || []).map((item) => ({
            period: item.period,
            ratio: item.ratio,
          })),
        });

        if (ignore) return;

        setComment(data.comment);
        setProbability(data.probability);
        setIsDummy(false);
      } catch (err) {
        console.error("get_graph_comment 호출 실패:", err);

        if (!ignore) {
          setComment(DUMMY_COMMENT.comment);
          setProbability(DUMMY_COMMENT.probability);
          setIsDummy(true);
        }
      } finally {
        if (!ignore) setLoading(false);
      }
    })();

    return () => {
      ignore = true;
    };
  }, [keyword, result]);

  if (loading) {
    return (
      <div className="graph-comment-card">
        <p className="graph-comment-loading">AI가 그래프를 분석하고 있습니다...</p>
      </div>
    );
  }

  const info = PROBABILITY_INFO[probability] || PROBABILITY_INFO.MEDIUM;

  return (
    <div className="graph-comment-card">
      <div className="graph-comment-header">
        <span className="graph-comment-badge" style={{ backgroundColor: info.color }}>
          {info.label}
        </span>
        {isDummy && <span className="dummy-badge">예시 데이터</span>}
      </div>

      <p className="graph-comment-text">{comment}</p>
    </div>
  );
}

export default GraphComment;