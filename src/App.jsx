import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import "./css/app.css";

import Sidebar from "./jsx/Sidebar";

import DashboardPage from "./pages/DashboardPage";
import KeywordPage from "./pages/KeywordPage";
import ComparePage from "./pages/ComparePage";
import TrendsPage from "./pages/TrendsPage";

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Sidebar />

        <main className="main">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" />} />

            <Route path="/dashboard" element={<DashboardPage />} />

            <Route path="/keyword" element={<KeywordPage />} />

            <Route path="/compare" element={<ComparePage />} />

            <Route path="/trends" element={<TrendsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
