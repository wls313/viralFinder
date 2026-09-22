import { useEffect, useState } from "react";
import { getGraphComment } from "../api/aiCommentApi";
import "../css/graphComment.css";

const PROBABILITY_INFO = {
  HIGH: { label: "상승 확률 높음", color: "#22c55e" },
  MEDIUM: { label: "상승 확률 보통", color: "#f59e0b" },
  LOW: { label: "상승 확률 낮음", color: "#ef4444" },
};

// aiAnalysis.trendStatus -> PROBABILITY_INFO 키 매핑
const TREND_STATUS_TO_PROBABILITY = {
  RISING: "HIGH",
  STABLE: "MEDIUM",
  DECLINING: "LOW",
};

// similarCases.outcome 배지 스타일
const OUTCOME_INFO = {
  FADED: { label: "급락 후 소멸", color: "#ef4444" },
  SUSTAINED: { label: "꾸준히 유지", color: "#22c55e" },
};

// 백엔드(Spring AI) 미기동/실패 시 보여줄 예시 데이터
const DUMMY_COMMENT = {
  comment:
    "탕후루의 현재 트렌드는 규칙 기반 통계 판정(math_prediction)에서 'STAY'를 나타내어 일시적인 안정세를 보이고 있습니다. 하지만 네이버 모멘텀이 'DOWN' (단기평균 45.7 / 장기평균 59.9)을 기록하며 하락 추세를 보이고 있고, 최근 X(트위터) 언급 샘플이 0건인 점은 사회적 관심도가 크게 감소했음을 시사합니다. 특히 과거 유사 사례에서 '탕후루'는 초반 31일 구간의 모양이 급격히 유행이 확산된 뒤 약 10일 만에 정점을 찍고 이후 빠르게 관심이 식어 정점 대비 28일 후 약 4.33% 수준까지 하락한 전형적인 'FADED' 유형의 급등-급락형 트렌드였습니다. 현재의 'STAY' 판정은 급격한 하락세 이후 낮은 관심도 수준에서 유지되거나 서서히 소멸하는 단계로 진입했음을 의미하며, 전반적인 트렌드 수명 주기는 이미 정점을 지나 쇠퇴 단계에 있다고 판단됩니다.",
  trendStatus: "DECLINING",
  mathPrediction: "STAY",
  probability: "LOW", // trendStatus(DECLINING) 기준 매핑
  similarCases: [
    {
      caseId: 5,
      keyword: "요아정",
      outcome: "FADED",
      summaryText:
        "빠르게 확산돼 정점을 찍은 뒤 서서히 식어, 정점 대비 28일 후 약 2.24% 수준으로 하락한 사례.",
      distance: 215.72343066485755,
    },
    {
      caseId: 2,
      keyword: "두바이초콜릿",
      outcome: "SUSTAINED",
      summaryText:
        "정점 이후에도 관심도가 급격히 꺼지지 않고 정점 대비 약 79.88% 수준에서 안착해 꾸준한 수요를 유지한 사례.",
      distance: 215.94822389502443,
    },
    // {
    //   caseId: 1,
    //   keyword: "탕후루",
    //   outcome: "FADED",
    //   summaryText:
    //     "급격히 유행이 확산된 뒤 약 10일 만에 정점을 찍었고, 이후 빠르게 관심이 식어 정점 대비 28일 후 약 4.33% 수준까지 하락한 전형적인 급등-급락형 사례.",
    //   distance: 235.6086264494906,
    // },
  ],
};

function GraphComment({ keyword, result }) {
  const [comment, setComment] = useState(null);
  const [probability, setProbability] = useState(null);
  const [similarCases, setSimilarCases] = useState([]);
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
      setSimilarCases(DUMMY_COMMENT.similarCases);
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

        // 백엔드 응답이 aiAnalysis 래핑 구조({ aiAnalysis, mathPrediction, similarCases })로 오는 경우 대응
        const resolvedComment = data.comment ?? data.aiAnalysis?.analysisReason;
        const resolvedProbability =
          data.probability ??
          TREND_STATUS_TO_PROBABILITY[data.aiAnalysis?.trendStatus] ??
          "MEDIUM";

        setComment(resolvedComment);
        setProbability(resolvedProbability);
        setSimilarCases(data.similarCases ?? []);
        setIsDummy(false);
      } catch (err) {
        console.error("get_graph_comment 호출 실패:", err);

        if (!ignore) {
          setComment(DUMMY_COMMENT.comment);
          setProbability(DUMMY_COMMENT.probability);
          setSimilarCases(DUMMY_COMMENT.similarCases);
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
      {/* 메인: AI 분석 코멘트 */}
      <div className="graph-comment-header">
        <span className="graph-comment-badge" style={{ backgroundColor: info.color }}>
          {info.label}
        </span>
        {isDummy && <span className="dummy-badge">예시 데이터</span>}
      </div>

      <p className="graph-comment-text">{comment}</p>

      {/* 서브: 유사 사례 - 메인 코멘트 아래, 카드 3개를 가로로 나열 */}
      {similarCases.length > 0 && (
        <div className="similar-cases-section">
          <h4 className="similar-cases-title">유사 사례</h4>
          <div className="similar-cases-grid">
            {similarCases.map((c) => {
              const outcomeInfo = OUTCOME_INFO[c.outcome] || {
                label: c.outcome,
                color: "#6b7280",
              };
              return (
                <div key={c.caseId} className="similar-case-card">
                  <div className="similar-case-card-header">
                    <span className="similar-case-keyword">{c.keyword}</span>
                    <span
                      className="similar-case-outcome"
                      style={{ backgroundColor: outcomeInfo.color }}
                    >
                      {outcomeInfo.label}
                    </span>
                  </div>
                  <p className="similar-case-summary">{c.summaryText}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export default GraphComment;