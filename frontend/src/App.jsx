import { useState } from 'react';

import './css/app.css';

import Sidebar from './jsx/Sidebar';
import Header from './jsx/Header';
import EmptyState from './jsx/EmptyState';
import Dashboard from './jsx/Dashboard';
import { searchKeyword } from "./api/searchApi";

function App() {
  const [keyword, setKeyword] = useState('');
  const [searchedKeyword, setSearchedKeyword] = useState('');
  const [result, setResult] = useState(null);

  const handleSearch = async () => {
  if (!keyword.trim()) return;

  try {
    const data = await searchKeyword(keyword);

    setResult(data);
    setSearchedKeyword(keyword);

  } catch (error) {
    console.error("API 호출 실패:", error);
  }
};

  return (
    <div className="app">
      <Sidebar />

      <main className="main">
        <Header
          keyword={keyword}
          setKeyword={setKeyword}
          handleSearch={handleSearch}
        />

        {!searchedKeyword ? (
          <EmptyState setKeyword={setKeyword} />
        ) : (
          <Dashboard
            keyword={searchedKeyword}
            result={result}
          />
        )}
      </main>
    </div>
  );
}

export default App;