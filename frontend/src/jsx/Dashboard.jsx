import StatsCards from './StatsCards';
import TrendChart from './TrendChart';
import AIAnalysis from './AIAnalysis';
import Timeline from './Timeline';
import RelatedKeywords from './RelatedKeywords';

import '../css/dashboard.css';


function Dashboard({ keyword, result }) {
  return (
    <section className="dashboard">
      <div className="dashboard-top">
        <div>
          <h2>{keyword}</h2>
          <p>실시간 분석 결과</p>
        </div>

      </div>

      <StatsCards result={result}/>

      <div className="dashboard-grid">
        <div className="left-content">
          <TrendChart result={result}/>

          <div className="bottom-grid">
            <Timeline />
            <RelatedKeywords />
          </div>
        </div>

        <AIAnalysis result={result}/>
      </div>
    </section>
  );
}

export default Dashboard;