import '../css/topContent.css';

// TODO(백엔드): 아직 "조회수 최고 유튜브 영상 / X 게시물"을 반환하는
// API가 없습니다. 백엔드에서 아래 형태로 result에 필드를 추가해주면
// 그대로 연결됩니다.
//   result.top_youtube = { url, content, createdAt }
//   result.top_x       = { url, content, createdAt }
// 지금은 더미 데이터로 화면만 미리 구성해뒀습니다.
const DUMMY_YOUTUBE = {
  url: "https://www.youtube.com/watch?v=dummy",
  content: "버터쿠키 만드는 법 - 초간단 레시피 브이로그",
  createdAt: "2026-07-28",
};

const DUMMY_X = {
  url: "https://x.com/dummyuser/status/000000",
  content: "요즘 다들 버터쿠키 만들어 먹던데 진짜 맛있어요 ㅠㅠ",
  createdAt: "2026-07-30",
};

function ContentCard({ platform, data, isDummy }) {
  if (!data) {
    return (
      <div className="content-card">
        <h4>{platform}</h4>
        <p className="content-empty">아직 데이터가 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="content-card">
      <div className="content-card-header">
        <h4>{platform}</h4>
        {isDummy && <span className="dummy-badge">예시 데이터</span>}
      </div>

      <p className="content-text">{data.content}</p>

      <div className="content-meta">
        <span>{data.createdAt}</span>
        <a href={data.url} target="_blank" rel="noreferrer">
          원본 보기 →
        </a>
      </div>
    </div>
  );
}

function TopContent({ result }) {
  // 실제 백엔드 데이터가 있으면 그걸 쓰고, 없으면 더미로 화면 형태만 보여줌
  const youtube = result?.top_youtube || DUMMY_YOUTUBE;
  const x = result?.top_x || DUMMY_X;

  return (
    <div className="top-content">
      <h3>조회수 최고 콘텐츠</h3>

      <div className="top-content-grid">
        <ContentCard
          platform="유튜브"
          data={youtube}
          isDummy={!result?.top_youtube}
        />

        <ContentCard
          platform="X (트위터)"
          data={x}
          isDummy={!result?.top_x}
        />
      </div>
    </div>
  );
}

export default TopContent;
