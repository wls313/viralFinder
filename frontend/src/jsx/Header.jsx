import '../css/header.css';

function Header({
    keyword,
    setKeyword,
    handleSearch,
    sidebarOpen,
    setSidebarOpen
}) {
  return (
    <header className="header">
      <button
        className="hamburger"
        onClick={() => setSidebarOpen(!sidebarOpen)}
      >
        ☰
      </button>
      
      <input
        type="text"
        placeholder="키워드를 입력하세요"
        value={keyword}
        onChange={(e) => setKeyword(e.target.value)}
        className="search-input"
      />

      <button
        className="search-btn"
        onClick={handleSearch}
      >
        분석하기
      </button>
    </header>
  );
}

export default Header;