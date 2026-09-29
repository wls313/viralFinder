import StatsCards from './StatsCards';
import TrendChart from './TrendChart';
import TopContent from './TopContent';
import GraphComment from './GraphComment'; // 추가

import '../css/dashboard.css';

const PERIOD_LABELS = {
  "1w": "최근 7일",
  "1m": "최근 30일",
  "3m": "최근 90일",
};

function Dashboard({ keyword, result, period = "1w", setPeriod }) {
  return (
    <section className="dashboard">
      <div className="dashboard-top">
        <div>
          <h2>{keyword}</h2>
          <p>
            {result?._dummy ? "더미 데이터 분석 결과" : "실시간 분석 결과"}
            {" · "}
            {PERIOD_LABELS[period] || PERIOD_LABELS["1w"]}
          </p>
        </div>
      </div>

      <StatsCards result={result}/>

      <div className="dashboard-grid">
        <div className="left-content">
          <TrendChart result={result} period={period} setPeriod={setPeriod}/>

          <GraphComment keyword={keyword} result={result}/>{/* 추가된 부분 */}

          <TopContent keyword={keyword}/>
        </div>
      </div>
    </section>
  );
}

export default Dashboard;
