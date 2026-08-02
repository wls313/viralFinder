import StatsCards from './StatsCards';
import TrendChart from './TrendChart';
import TopContent from './TopContent';
// AIAnalysis: 대시보드에서 AI 분석결과 패널 숨김 처리 (요청사항)
// import AIAnalysis from './AIAnalysis';
// Timeline("급상승 원인"), RelatedKeywords("연관 키워드"): 키워드 분석 화면에서 숨김 처리 (더미 데이터)
// import Timeline from './Timeline';
// import RelatedKeywords from './RelatedKeywords';

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

          <TopContent result={result} />

          {/* <div className="bottom-grid">
            <Timeline />
            <RelatedKeywords />
          </div> */}
        </div>

        {/* <AIAnalysis result={result}/> */}
      </div>
    </section>
  );
}

export default Dashboard;
