import '../css/header.css';

export const PERIOD_PRESETS = [
  { key: "1w", label: "1주일" },
  { key: "1m", label: "1달" },
  { key: "3m", label: "3달" },
];

// 그래프 카드 안에 들어가는 기간 선택 버튼 (기존 Header의 .period-presets 스타일 재사용)
function PeriodSelector({ period, setPeriod }) {
  return (
    <div className="period-presets">
      {PERIOD_PRESETS.map(({ key, label }) => (
        <button
          key={key}
          type="button"
          className={`period-btn ${period === key ? "active" : ""}`}
          onClick={() => setPeriod(key)}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

export default PeriodSelector;
