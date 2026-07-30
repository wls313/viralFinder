import StatsCards from './StatsCards';
import TrendChart from './TrendChart';
import AIAnalysis from './AIAnalysis';
import Timeline from './Timeline';
import RelatedKeywords from './RelatedKeywords';

import '../css/dashboard.css';


function Dashboard({ keyword, result }) {
  return (
    <section className="dashboard">

      <StatsCards result={result}/>

      <div className="dashboard-grid">
        <div className="left-content">
          <TrendChart result={result}/>
          {/*
          <div className="bottom-grid">
            <Timeline />
            <RelatedKeywords />
          </div>
          */}
        </div>

        <AIAnalysis result={result}/>
      </div>
    </section>
  );
}

export default Dashboard;