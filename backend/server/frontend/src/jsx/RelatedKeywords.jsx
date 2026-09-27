function RelatedKeywords() {
  return (
    <div className="card">
      <h3>연관 키워드</h3>

      <div
        style={{
          marginTop: '20px',
          display: 'flex',
          gap: '10px',
          flexWrap: 'wrap',
        }}
      >
        <span>쿠키맛집</span>
        <span>디저트</span>
        <span>간식</span>
      </div>
    </div>
  );
}

export default RelatedKeywords;