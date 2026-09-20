import { useEffect, useState } from 'react';

import './css/app.css';

import Sidebar from './jsx/Sidebar';
import Header from './jsx/Header';
import EmptyState from './jsx/EmptyState';
import Dashboard from './jsx/Dashboard';
import { searchKeyword } from "./api/searchApi";
import { getTrendsData } from "./api/trendsApi";
import LoadingPage from './pages/LoadingPage';
import TrendsPage from './pages/TrendsPage';

function App() {
  const [keyword, setKeyword] = useState('');
  const [searchedKeyword, setSearchedKeyword] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState("trends");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  // 검색조건 프리셋: 1주일 / 1달 / 3달 (백엔드에 아직 기간 파라미터가 없어서
  // 우선 프론트에서 값만 보내둠. 백엔드팀에게 period 파라미터 반영 요청 필요)
  const [period, setPeriod] = useState("1w");
  // 검색화면(EmptyState)에 보여줄 1~3위 키워드.
  // 실시간 트렌드 API가 아직 없어서 trendsApi의 mock 데이터를 사용 중이고,
  // 백엔드에 실제 트렌드 엔드포인트가 생기면 getTrendsData 구현부만 교체하면
  // 여기는 그대로 동작함.
  const [topKeywords, setTopKeywords] = useState([]);

  useEffect(() => {
    let ignore = false;

    getTrendsData("all", "growth").then((data) => {
      if (!ignore) {
        setTopKeywords(data.slice(0, 3).map((item) => item.keyword));
      }
    });

    return () => {
      ignore = true;
    };
  }, []);

  const handleSearch = async () => {
    if (!keyword.trim()) return;

    setLoading(true);

    try {
      const data = await searchKeyword(keyword, period);

      setResult(data);
      setSearchedKeyword(keyword);
      setCurrentPage("analysis");

    } catch (error) {
      console.error("API 호출 실패:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`app ${sidebarCollapsed ? "sidebar-collapsed" : ""}`}>
      <Sidebar
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        collapsed={sidebarCollapsed}
        setCollapsed={setSidebarCollapsed}
      />

      <main className="main">
        <Header
          keyword={keyword}
          setKeyword={setKeyword}
          handleSearch={handleSearch}
          period={period}
          setPeriod={setPeriod}
        />

        {currentPage === "trends" ? (
          <TrendsPage />
        ) : loading ? (
          <LoadingPage />
        ) : currentPage === "analysis" ? (
          <Dashboard
            keyword={searchedKeyword}
            result={result}
          />
        ) : (
          <EmptyState setKeyword={setKeyword} topKeywords={topKeywords} />
        )}
      </main>
    </div>
  );
}

export default App;