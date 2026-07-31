import { useState } from 'react';

import './css/app.css';

import Sidebar from './jsx/Sidebar';
import Header from './jsx/Header';
import EmptyState from './jsx/EmptyState';
import Dashboard from './jsx/Dashboard';
import { searchKeyword } from "./api/searchApi";
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
          <EmptyState setKeyword={setKeyword} />
        )}
      </main>
    </div>
  );
}

export default App;