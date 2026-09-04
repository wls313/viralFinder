import { useEffect, useState } from "react";
import { getRecommendedVideo, getRecommendedTweet } from "../api/rankingApi";
import '../css/topContent.css';

// 백엔드 랭킹 API가 반환하는 필드: {type, url, full_text, created_at}
const DUMMY_YOUTUBE = {
  url: "https://www.youtube.com/watch?v=dummy",
  full_text: "버터쿠키 만드는 법 - 초간단 레시피 브이로그",
  created_at: "2026-07-28",
};

const DUMMY_X = {
  url: "https://x.com/dummyuser/status/000000",
  full_text: "요즘 다들 버터쿠키 만들어 먹던데 진짜 맛있어요 ㅠㅠ",
  created_at: "2026-07-30",
};

function ContentCard({ platform, data, isDummy, loading }) {
  if (loading) {
    return (
      <div className="content-card">
        <h4>{platform}</h4>
        <p className="content-empty">불러오는 중...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="content-card">
        <h4>{platform}</h4>
        <p className="content-empty">아직 데이터가 없습니다.</p>
      </div>
    );
  }

  return (
    <a
      className="content-card content-card-link"
      href={data.url}
      target="_blank"
      rel="noreferrer"
    >
      <div className="content-card-header">
        <h4>{platform}</h4>
        {isDummy && <span className="dummy-badge">예시 데이터</span>}
      </div>

      <p className="content-text">{data.full_text}</p>

      <div className="content-meta">
        <span>{data.created_at}</span>
        <span className="content-link-hint">원본 보기 →</span>
      </div>
    </a>
  );
}

function TopContent({keyword}) {
  const [youtube, setYoutube] = useState(null);
  const [x, setX] = useState(null);
  const [loading, setLoading] = useState(true);
  const [youtubeIsDummy, setYoutubeIsDummy] = useState(false);
  const [xIsDummy, setXIsDummy] = useState(false);

  useEffect(() => {
    let ignore = false;


    (async () => {
      const [videoRes, tweetRes] = await Promise.allSettled([
        getRecommendedVideo(keyword),
        getRecommendedTweet(keyword),
      ]);

      if (ignore) return;

      if (videoRes.status === "fulfilled" && videoRes.value?.data?.length > 0) {
        setYoutube(videoRes.value.data[0]);
      } else {
        if (videoRes.status === "rejected") {
          console.error("get_recommended_video 호출 실패:", videoRes.reason);
        }
        setYoutube(DUMMY_YOUTUBE);
        setYoutubeIsDummy(true);
      }

      if (tweetRes.status === "fulfilled" && tweetRes.value?.data?.length > 0) {
        setX(tweetRes.value.data[0]);
      } else {
        if (tweetRes.status === "rejected") {
          console.error("get_recommended_tweet 호출 실패:", tweetRes.reason);
        }
        setX(DUMMY_X);
        setXIsDummy(true);
      }

      setLoading(false);
    })();

    return () => {
      ignore = true;
    };
  }, []);

  return (
    <div className="top-content">
      <h3>조회수 최고 콘텐츠</h3>

      <div className="top-content-grid">
        <ContentCard platform="유튜브" data={youtube} isDummy={youtubeIsDummy} loading={loading} />
        <ContentCard platform="X (트위터)" data={x} isDummy={xIsDummy} loading={loading} />
      </div>
    </div>
  );
}

export default TopContent;