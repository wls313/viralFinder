import { useEffect, useState } from "react";
import { getGraphComment } from "../api/aiCommentApi";
import "../css/graphComment.css";

const PROBABILITY_INFO = {
  HIGH: { label: "상승 확률 높음", color: "#22c55e" },
  MEDIUM: { label: "상승 확률 보통", color: "#f59e0b" },
  LOW: { label: "상승 확률 낮음", color: "#ef4444" },
};

// min Spring AI TrendDto.TrendStatus -> PROBABILITY_INFO 키 매핑
const TREND_STATUS_TO_PROBABILITY = {
  RISING: "HIGH",
  PEAKING: "MEDIUM",
  STABLE: "MEDIUM",
  DECLINING: "LOW",
  INSUFFICIENT_DATA: "LOW",
};

// similarCases.outcome 배지 스타일
const OUTCOME_INFO = {
  FADED: { label: "급락 후 소멸", color: "#ef4444" },
  SUSTAINED: { label: "꾸준히 유지", color: "#22c55e" },
  REIGNITED: { label: "재점화", color: "#f59e0b" },
};

// 백엔드(Spring AI) 미기동/실패 시 보여줄 예시 데이터
const DUMMY_COMMENT = {
  comment:
    "탕후루의 현재 트렌드는 규칙 기반 통계 판정(math_prediction)에서 'STAY'를 나타내어 일시적인 안정세를 보이고 있습니다. 하지만 네이버 모멘텀이 'DOWN' (단기평균 45.7 / 장기평균 59.9)을 기록하며 하락 추세를 보이고 있고, 최근 X(트위터) 언급 샘플이 0건인 점은 사회적 관심도가 크게 감소했음을 시사합니다. 특히 과거 유사 사례에서 '탕후루'는 초반 31일 구간의 모양이 급격히 유행이 확산된 뒤 약 10일 만에 정점을 찍고 이후 빠르게 관심이 식어 정점 대비 28일 후 약 4.33% 수준까지 하락한 전형적인 'FADED' 유형의 급등-급락형 트렌드였습니다. 현재의 'STAY' 판정은 급격한 하락세 이후 낮은 관심도 수준에서 유지되거나 서서히 소멸하는 단계로 진입했음을 의미하며, 전반적인 트렌드 수명 주기는 이미 정점을 지나 쇠퇴 단계에 있다고 판단됩니다.",
  trendStatus: "DECLINING",
  mathPrediction: "STAY",
  probability: "LOW",
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
  ],
};

// AI 코멘트는 검색 1회당 한 번만 요청한다(기간 버튼을 눌러도 다시 호출하지 않음).
// Spring AI는 period를 그대로 파이썬 /api/analysis 로 넘기므로 숫자(일수) 문자열로 보낸다.
const COMMENT_PERIOD = "90";

// 실패 원인을 사용자가 바로 알 수 있도록 문장으로 변환
const describeError = (err) => {
  if (err?.code === "ECONNABORTED") {
    return "AI 분석 응답 시간이 초과되었습니다. (Spring AI / Gemini 응답 지연)";
  }
  if (err?.response) {
    const { status, data } = err.response;
    const detail =
      typeof data === "string"
        ? data
        : data?.message || data?.detail || data?.error;
    return `AI 분석 서버 오류 (HTTP ${status})${detail ? `: ${detail}` : ""}`;
  }
  if (err?.request) {
    return "AI 분석 서버(localhost:8080)에 연결할 수 없습니다. Spring AI가 실행 중인지 확인하세요.";
  }
  return err?.message || "알 수 없는 오류가 발생했습니다.";
};

function GraphComment({ keyword, result }) {
  const [comment, setComment] = useState(null);
  const [probability, setProbability] = useState(null);
  const [similarCases, setSimilarCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDummy, setIsDummy] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [noData, setNoData] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    let ignore = false;

    const showExample = () => {
      setComment(DUMMY_COMMENT.comment);
      setProbability(DUMMY_COMMENT.probability);
      setSimilarCases(DUMMY_COMMENT.similarCases);
      setIsDummy(true);
      setLoading(false);
    };

    setErrorMessage(null);
    setNoData(false);

    // 1) 아직 검색한 적이 없을 때만 예시(탕후루)를 보여준다.
    if (!result) {
      showExample();
      return;
    }

    // 2) 더미 데이터 모드: 더미 JSON에 포함된 ai_comment를 그대로 사용 (Spring AI 호출 생략)
    if (result._dummy && result.ai_comment) {
      setComment(result.ai_comment.comment);
      setProbability(result.ai_comment.probability);
      setSimilarCases(result.ai_comment.similarCases ?? []);
      setIsDummy(true);
      setLoading(false);
      return;
    }

    // 3) 검색은 했지만 수집된 트렌드 데이터가 없을 때: 예시로 덮지 않고 안내
    const hasTrendData =
      result.naver_trend?.length ||
      result.google_trend?.length ||
      result.x_trend?.length ||
      result.twitter_trends?.length;

    if (!hasTrendData) {
      setNoData(true);
      setLoading(false);
      return;
    }

    // 4) 실제 Spring AI 분석 요청
    (async () => {
      setLoading(true);

      try {
        // Spring AI: GET /api/trends/recommend?keyword=...&period=90
        // Spring AI가 Python 백엔드에서 데이터를 가져오므로 keyword/period만 전달
        const data = await getGraphComment({
          keyword,
          period: COMMENT_PERIOD,
          // 검색할 때마다 바뀌는 updated_at을 키에 넣어, 새 검색이면 새로 분석하고
          // 같은 검색 결과면(재마운트, StrictMode) 이전 요청을 재사용한다.
          cacheKey: `${keyword}|${result.updated_at ?? ""}|${retryCount}`,
        });

        if (ignore) return;

        // TrendAnalysisResult 구조:
        // { aiAnalysis: { trendStatus, analysisReason, recommendedItems },
        //   mathPrediction, similarCases: [{ caseId, keyword, outcome, summaryText, distance }] }
        const resolvedComment =
          data?.comment ??
          data?.aiAnalysis?.analysisReason ??
          data?.analysisReason ??
          null;

        const trendStatus =
          data?.aiAnalysis?.trendStatus ?? data?.trendStatus ?? null;

        const resolvedProbability =
          data?.probability ??
          TREND_STATUS_TO_PROBABILITY[trendStatus] ??
          "MEDIUM";

        const cases = data?.similarCases ?? data?.matchedCases ?? [];

        setComment(resolvedComment);
        setProbability(resolvedProbability);
        setSimilarCases(Array.isArray(cases) ? cases : []);
        setIsDummy(false);
      } catch (err) {
        console.error("get_graph_comment 호출 실패:", err);

        // 실패했을 때 탕후루 예시로 덮으면 실제 분석인 것처럼 오해되므로
        // 실패 사유와 "다시 시도" 버튼을 보여준다.
        if (!ignore) setErrorMessage(describeError(err));
      } finally {
        if (!ignore) setLoading(false);
      }
    })();

    return () => {
      ignore = true;
    };
  }, [keyword, result, retryCount]);

  if (loading) {
    return (
      <div className="graph-comment-card">
        <p className="graph-comment-loading">AI가 그래프를 분석하고 있습니다...</p>
      </div>
    );
  }

  if (errorMessage) {
    return (
      <div className="graph-comment-card">
        <p className="graph-comment-error">AI 분석을 불러오지 못했습니다.</p>
        <p className="graph-comment-error-detail">{errorMessage}</p>
        <button
          type="button"
          className="graph-comment-retry-btn"
          onClick={() => setRetryCount((n) => n + 1)}
        >
          다시 시도
        </button>
      </div>
    );
  }

  if (noData) {
    return (
      <div className="graph-comment-card">
        <p className="graph-comment-loading">
          수집된 트렌드 데이터가 없어 AI 분석을 건너뛰었습니다.
        </p>
      </div>
    );
  }

  const info = PROBABILITY_INFO[probability] || PROBABILITY_INFO.MEDIUM;

  return (
    <div className="graph-comment-card">
      {/* 메인: AI 분석 코멘트 */}
      <div className="graph-comment-header">
        <span
          className="graph-comment-badge"
          style={{ backgroundColor: info.color }}
        >
          {info.label}
        </span>
        {isDummy && <span className="dummy-badge">예시 데이터</span>}
      </div>

      <p className="graph-comment-text">{comment}</p>

      {/* 서브: 유사 사례 */}
      {similarCases.length > 0 && (
        <div className="similar-cases-section">
          <h4 className="similar-cases-title">유사 사례</h4>
          <div className="similar-cases-grid">
            {similarCases.map((c) => {
              const outcomeInfo = OUTCOME_INFO[c.outcome] || {
                label: c.outcome || "알 수 없음",
                color: "#6b7280",
              };
              return (
                <div key={c.caseId ?? c.keyword} className="similar-case-card">
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
