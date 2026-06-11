import { useState } from "react";

import Header from "../jsx/Header";
import EmptyState from "../jsx/EmptyState";
import Dashboard from "../jsx/Dashboard";

function DashboardPage() {
  const [keyword, setKeyword] = useState("");
  const [searchedKeyword, setSearchedKeyword] = useState("");

  const handleSearch = () => {
    if (!keyword.trim()) return;

    setSearchedKeyword(keyword);
  };

  return (
    <>
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
    </>
  );
}

export default DashboardPage;
