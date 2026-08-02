import '../css/sidebar.css';

const MENU_ITEMS = [
  { key: "trends", label: "트렌드", icon: "📈" },
  { key: "dashboard", label: "대시보드", icon: "🔍" },
  { key: "analysis", label: "키워드 분석", icon: "🧠" },
];

function Sidebar({ currentPage, setCurrentPage, collapsed, setCollapsed }) {
  return (
    <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      <div>
        <div className="sidebar-top">
          {!collapsed && (
            <div className="logo">
              <h1>Trend Tracker</h1>
              <p>TT</p>
            </div>
          )}

          <button
            className="hamburger-btn"
            onClick={() => setCollapsed((prev) => !prev)}
            aria-label="사이드바 접기/펼치기"
          >
            ☰
          </button>
        </div>

        <nav className="menu">
          {MENU_ITEMS.map(({ key, label, icon }) => (
            <button
              key={key}
              className={`menu-item ${currentPage === key ? "active" : ""}`}
              onClick={() => setCurrentPage(key)}
              title={label}
            >
              <span className="menu-icon">{icon}</span>
              {!collapsed && <span className="menu-label">{label}</span>}
            </button>
          ))}
        </nav>
      </div>
    </aside>
  );
}

export default Sidebar;