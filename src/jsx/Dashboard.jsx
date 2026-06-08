import StatsCards from './StatsCards';
import TrendChart from './TrendChart';
import AIAnalysis from './AIAnalysis';
import Timeline from './Timeline';
import RelatedKeywords from './RelatedKeywords';

import '../css/dashboard.css';

const mockResult = {
  status: '바이럴 의심',
  score: 54.2,
};

function Dashboard({ keyword }) {
  return (
    <section className="dashboard">
      <div className="dashboard-top">
        <div>
          <h2>{keyword}</h2>
          <p>실시간 분석 결과</p>
        </div>

        <button className="compare-btn">
          키워드 비교
        </button>
      </div>

      <StatsCards />

      <div className="dashboard-grid">
        <div className="left-content">
          <TrendChart />

          <div className="bottom-grid">
            <Timeline />
            <RelatedKeywords />
          </div>
        </div>

        <AIAnalysis result={mockResult}/>
      </div>
    </section>
  );
}

export default Dashboard;