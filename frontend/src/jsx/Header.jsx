import '../css/header.css';

const PERIOD_PRESETS = [
  { key: "1w", label: "1주일" },
  { key: "1m", label: "1달" },
  { key: "3m", label: "3달" },
];

function Header({
  keyword,
  setKeyword,
  handleSearch,
  period,
  setPeriod,
}) {
  return (
    <header className="header">
      <div className="search-row">
        <input
          type="text"
          placeholder="키워드를 입력하세요"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          className="search-input"
        />

        <button
          className="search-btn"
          onClick={handleSearch}
        >
          분석하기
        </button>
      </div>

      {setPeriod && (
        <div className="period-presets">
          {PERIOD_PRESETS.map(({ key, label }) => (
            <button
              key={key}
              className={`period-btn ${period === key ? "active" : ""}`}
              onClick={() => setPeriod(key)}
            >
              {label}
            </button>
          ))}
        </div>
      )}
    </header>
  );
}

export default Header;