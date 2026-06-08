import { useState } from 'react';

import './css/app.css';

import Sidebar from './jsx/Sidebar';
import Header from './jsx/Header';
import EmptyState from './jsx/EmptyState';
import Dashboard from './jsx/Dashboard';

function App() {
  const [keyword, setKeyword] = useState('');
  const [searchedKeyword, setSearchedKeyword] = useState('');

  const handleSearch = () => {
    if (!keyword.trim()) return;

    setSearchedKeyword(keyword);
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
          <Dashboard keyword={searchedKeyword} />
        )}
      </main>
    </div>
  );
}

export default App;