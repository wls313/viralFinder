import React, { useState, useEffect } from "react";
import "../css/MainScreen.css";

const MainScreen = ({ onSearch }) => {
  const [inputValue, setInputValue] = useState("");
  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState([]);

  // 1. 처음 앱이 켜질 때 브라우저 저장소(LocalStorage)에서 기록 불러오기
  useEffect(() => {
    const savedHistory = localStorage.getItem("viralFinderHistory");
    if (savedHistory) {
      setHistory(JSON.parse(savedHistory));
    }
  }, []);

  // 2. 검색 실행 함수
  const handleSearch = () => {
    if (inputValue.trim()) {
      // 1. 새로운 기록 추가 (기존 로직 동일)
      const newHistory = [
        { id: Date.now(), text: inputValue },
        ...history.filter((item) => item.text !== inputValue),
      ].slice(0, 5);

      setHistory(newHistory);
      localStorage.setItem("viralFinderHistory", JSON.stringify(newHistory));

      // 2. 부모 컴포넌트(App.jsx)의 함수를 호출하여 화면 전환 (중요!)
      onSearch(inputValue);

      // 3. 뒷정리
      setInputValue(""); // 입력창 초기화
      setShowHistory(false); // 히스토리 창 닫기
    }
  };

  // 3. 기록 삭제 함수
  const handleDelete = (id, e) => {
    e.stopPropagation(); // 드롭다운 닫힘 방지
    const filteredHistory = history.filter((item) => item.id !== id);
    setHistory(filteredHistory);
    localStorage.setItem("viralFinderHistory", JSON.stringify(filteredHistory));
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleSearch();
  };

  return (
    <div className="main-page">
      {/* 배경 장식용 효과 */}
      <div className="background-glow"></div>

      <main className="hero-section">
        <h1 className="hero-title">ViralFinder</h1>

        <div className="search-container">
          <div className="search-glass-box">
            <span className="search-icon-left">🔍</span>
            <input
              type="text"
              placeholder="내용을 입력하세요. (예: '챗GPT', '마케팅 트렌드')"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => setShowHistory(true)}
              onBlur={() => setTimeout(() => setShowHistory(false), 200)}
            />
            <button
              className="dropdown-arrow"
              onClick={() => setShowHistory(!showHistory)}
            >
              {showHistory ? "▲" : "▼"}
            </button>

            {/* 검색 기록 드롭다운 */}
            {showHistory && history.length > 0 && (
              <ul className="history-dropdown">
                {history.map((item) => (
                  <li key={item.id} onClick={() => setInputValue(item.text)}>
                    <span className="history-text">{item.text}</span>
                    <button
                      className="del-btn"
                      onClick={(e) => handleDelete(item.id, e)}
                    >
                      삭제
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <button className="search-submit-btn" onClick={handleSearch}>
            검색 <span className="btn-icon">🔍</span>
          </button>
        </div>
      </main>
    </div>
  );
};

export default MainScreen;
