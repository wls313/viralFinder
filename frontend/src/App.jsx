import { useEffect, useRef, useState } from 'react';

import './css/app.css';

import Sidebar from './jsx/Sidebar';
import Header from './jsx/Header';
import EmptyState from './jsx/EmptyState';
import Dashboard from './jsx/Dashboard';
import { searchKeyword } from "./api/searchApi";
import { loadDummySearch } from "./api/dummySearch";
import { getTrendsData } from "./api/trendsApi";
import LoadingPage from './pages/LoadingPage';
import TrendsPage from './pages/TrendsPage';

const DUMMY_STORAGE_KEY = "viralFinder.useDummyData";

// 검색은 항상 "최대 범위(90일)"로 한 번만 수행한다.
// 1주일/1달/3달 버튼은 이미 받아온 90일치 데이터를 화면에서 잘라 보여줄 뿐,
// 백엔드를 다시 호출(크롤링)하지 않는다.
const FETCH_PERIOD = "3m";

// localStorage 접근 실패(시크릿 모드 등)에도 앱이 죽지 않도록 try/catch 처리
const readStoredDummyFlag = () => {
  try {
    return localStorage.getItem(DUMMY_STORAGE_KEY) === "true";
  } catch {
    return false;
  }
};

function App() {
  const [keyword, setKeyword] = useState('');
  const [searchedKeyword, setSearchedKeyword] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState("trends");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  // 검색조건 프리셋: 1주일(7일) / 1달(30일) / 3달(90일)
  const [period, setPeriod] = useState("1w");
  // 사이드바 하단 토글. ON이면 API 대신 dummySearchResults.json 사용
  const [useDummyData, setUseDummyData] = useState(readStoredDummyFlag);
  // 검색화면(EmptyState)에 보여줄 1~3위 키워드.
  // 실시간 트렌드 API가 아직 없어서 trendsApi의 mock 데이터를 사용 중이고,
  // 백엔드에 실제 트렌드 엔드포인트가 생기면 getTrendsData 구현부만 교체하면
  // 여기는 그대로 동작함.
  const [topKeywords, setTopKeywords] = useState([]);

  // 검색을 연달아 실행할 때, 늦게 도착한 이전 응답이 최신 결과를 덮어쓰지 않도록 하는 요청 번호
  const requestIdRef = useRef(0);

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

  useEffect(() => {
    try {
      localStorage.setItem(DUMMY_STORAGE_KEY, String(useDummyData));
    } catch {
      // 저장 실패는 무시 (새로고침 후 유지만 안 될 뿐 동작에는 영향 없음)
    }
  }, [useDummyData]);

  // 검색 실행: 항상 90일치 전체 데이터를 받아 result에 그대로 저장한다.
  // (period에 따른 7/30/90일 자르기는 TrendChart에서 표시 시점에 처리)
  const handleSearch = async () => {
    const trimmed = keyword.trim();
    if (!trimmed) return;

    const requestId = ++requestIdRef.current;
    setLoading(true);

    try {
      const data = useDummyData
        ? await loadDummySearch(trimmed)
        : await searchKeyword(trimmed, FETCH_PERIOD);

      // 더 최신 요청이 있으면 이 응답은 버림
      if (requestId !== requestIdRef.current) return;

      setResult(data);
      // 더미 폴백 시에는 실제로 로드된 키워드를 표시
      setSearchedKeyword(useDummyData ? data.keyword_name || trimmed : trimmed);
      setCurrentPage("analysis");
    } catch (error) {
      console.error("API 호출 실패:", error);
    } finally {
      if (requestId === requestIdRef.current) setLoading(false);
    }
  };

  return (
    <div className={`app ${sidebarCollapsed ? "sidebar-collapsed" : ""}`}>
      <Sidebar
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        collapsed={sidebarCollapsed}
        setCollapsed={setSidebarCollapsed}
        useDummyData={useDummyData}
        setUseDummyData={setUseDummyData}
      />

      <main className="main">
        <Header
          keyword={keyword}
          setKeyword={setKeyword}
          handleSearch={handleSearch}
        />

        {currentPage === "trends" ? (
          <TrendsPage />
        ) : loading ? (
          <LoadingPage />
        ) : currentPage === "analysis" ? (
          <Dashboard
            keyword={searchedKeyword}
            result={result}
            period={period}
            setPeriod={setPeriod}
          />
        ) : (
          <EmptyState setKeyword={setKeyword} topKeywords={topKeywords} />
        )}
      </main>
    </div>
  );
}

export default App;
