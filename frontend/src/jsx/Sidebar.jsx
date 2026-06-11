import '../css/sidebar.css';

function Sidebar() {
  return (
    <aside className="sidebar">
      <div>
        <div className="logo">
          <h1>ViralCheck</h1>
          <p>바이럴 분석 플랫폼</p>
        </div>

        <nav className="menu">
          <button className="menu-item active">
            대시보드
          </button>

          <button className="menu-item">
            키워드 분석
          </button>

          <button className="menu-item">
            비교 분석
          </button>

          <button className="menu-item">
            트렌드
          </button>
        </nav>
      </div>

      <div className="extension-box">
        <h3>Chrome 확장프로그램</h3>

        <p>
          검색 결과에서 광고 여부를
          분석합니다.
        </p>

        <button className="download-btn">
          다운로드
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;