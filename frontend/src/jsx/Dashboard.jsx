import StatsCards from './StatsCards';
import TrendChart from './TrendChart';
import TopContent from './TopContent';
import GraphComment from './GraphComment'; // 추가

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

          <GraphComment keyword={keyword} result={result}/>{/* 추가된 부분 */}

          <TopContent keyword={keyword}/>
        </div>
      </div>
    </section>
  );
}

export default Dashboard;