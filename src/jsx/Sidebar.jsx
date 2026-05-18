import { NavLink } from "react-router-dom";

import "../css/sidebar.css";

function Sidebar() {
  return (
    <aside className="sidebar">
      <div>
        <div className="logo">
          <h1>ViralCheck</h1>
          <p>바이럴 분석 플랫폼</p>
        </div>

        <nav className="menu">
          <NavLink
            to="/dashboard"
            className={({ isActive }) =>
              isActive ? "menu-item active" : "menu-item"
            }
          >
            대시보드
          </NavLink>

          <NavLink
            to="/keyword"
            className={({ isActive }) =>
              isActive ? "menu-item active" : "menu-item"
            }
          >
            키워드 분석
          </NavLink>

          <NavLink
            to="/compare"
            className={({ isActive }) =>
              isActive ? "menu-item active" : "menu-item"
            }
          >
            비교 분석
          </NavLink>

          <NavLink
            to="/trends"
            className={({ isActive }) =>
              isActive ? "menu-item active" : "menu-item"
            }
          >
            트렌드
          </NavLink>
        </nav>
      </div>

      <div className="extension-box">
        <h3>Chrome 확장프로그램</h3>

        <p>검색 결과에서 광고 여부를 분석합니다.</p>

        <button className="download-btn">다운로드</button>
      </div>
    </aside>
  );
}

export default Sidebar;
