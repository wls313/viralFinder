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
  const [currentPage, setCurrentPage] = useState("dashboard");

  const handleSearch = async () => {
    if (!keyword.trim()) return;

    setLoading(true);

    try {
      const data = await searchKeyword(keyword);

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
    <div className="app">
      <Sidebar
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
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
          />
        ) : (
          <EmptyState setKeyword={setKeyword} />
        )}
      </main>
    </div>
  );
}

export default App;