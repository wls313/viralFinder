import dummySearchResults from "../data/dummySearchResults.json";

// 기간 프리셋(1w/1m/3m) → 일수. searchApi.js의 periodMap(7/30/90)과 동일한 기준.
export const PERIOD_DAYS = {
  "1w": 7,
  "1m": 30,
  "3m": 90,
};

const normalize = (value) => String(value ?? "").trim().toLowerCase();

/**
 * 시계열(naver_trend / google_trend)에서 "가장 최근 날짜 기준" 최근 N일만 남긴다.
 * - 오늘 날짜가 아니라 데이터의 마지막 날짜를 기준으로 자르므로
 *   더미(고정 날짜)와 실데이터 모두 동일하게 동작한다.
 */
export const sliceTrendByPeriod = (trend, period) => {
  if (!Array.isArray(trend) || trend.length === 0) return [];

  const days = PERIOD_DAYS[period] || PERIOD_DAYS["1w"];
  const sorted = [...trend].sort((a, b) =>
    String(a.period).localeCompare(String(b.period))
  );

  const latest = new Date(sorted[sorted.length - 1].period);
  if (Number.isNaN(latest.getTime())) return sorted.slice(-days);

  const cutoff = new Date(latest);
  cutoff.setDate(cutoff.getDate() - (days - 1));

  const filtered = sorted.filter((item) => new Date(item.period) >= cutoff);
  return filtered.length > 0 ? filtered : sorted.slice(-days);
};

/**
 * 검색 결과(result)의 시계열을 period에 맞게 잘라 새 객체로 반환한다.
 * 원본은 변경하지 않는다.
 */
export const applyPeriod = (result, period) => {
  if (!result) return result;

  return {
    ...result,
    naver_trend: sliceTrendByPeriod(result.naver_trend, period),
    google_trend: sliceTrendByPeriod(result.google_trend, period),
    selected_period: period,
  };
};

/**
 * 더미 검색.
 * 1) keyword 매칭(trim, 대소문자 무시) → 해당 결과
 * 2) 매칭 실패 → 더미 중 무작위 1건
 * 반환값은 실제 API 응답과 같은 구조이며, 더미 표시용으로
 * _dummy(true) / _matched(매칭 여부) 필드만 추가된다.
 */
export const loadDummySearch = async (keyword) => {
  const list = dummySearchResults?.results ?? [];

  if (list.length === 0) {
    throw new Error("더미 데이터가 비어 있습니다.");
  }

  const target = normalize(keyword);
  const matched = list.find(
    (item) =>
      normalize(item.keyword) === target ||
      normalize(item.keyword_name) === target
  );

  const picked = matched ?? list[Math.floor(Math.random() * list.length)];

  return {
    ...picked,
    _dummy: true,
    _matched: Boolean(matched),
  };
};

// 기간별 묶음 단위(일): 7일=1일, 30일=3일, 90일=10일
export const BUCKET_DAYS = {
  "1w": 1,
  "1m": 3,
  "3m": 10,
};

const DAY_MS = 24 * 60 * 60 * 1000;

const toUtcMs = (ymd) => {
  const [y, m, d] = String(ymd).slice(0, 10).split("-").map(Number);
  return Date.UTC(y, m - 1, d);
};

const fmtYmd = (ms) => new Date(ms).toISOString().slice(0, 10);

const average = (values) => {
  const valid = values.filter((v) => typeof v === "number" && !Number.isNaN(v));
  if (valid.length === 0) return null;
  return Math.round((valid.reduce((a, b) => a + b, 0) / valid.length) * 10) / 10;
};

/**
 * 일 단위로 병합된 행(rows: [{ fullDate: "YYYY-MM-DD", naver, google, x }])을
 * period에 맞는 간격으로 묶어 평균값으로 줄인다.
 * - 가장 최근 날짜를 기준으로 뒤에서부터 묶기 때문에 마지막 구간이 항상 꽉 찬다.
 *   (90일 → 10일씩 9개, 30일 → 3일씩 10개, 7일 → 하루씩 7개)
 * - 묶음 구간 안에 값이 없는 지표는 null로 남는다.
 */
export const bucketRows = (rows, period, keys = ["naver", "google", "x"]) => {
  const step = BUCKET_DAYS[period] || 1;
  if (!Array.isArray(rows) || rows.length === 0 || step === 1) return rows || [];

  const sorted = [...rows].sort((a, b) => a.fullDate.localeCompare(b.fullDate));
  const latestMs = toUtcMs(sorted[sorted.length - 1].fullDate);

  const buckets = new Map();
  sorted.forEach((row) => {
    const diff = Math.round((latestMs - toUtcMs(row.fullDate)) / DAY_MS);
    const idx = Math.floor(diff / step);
    if (!buckets.has(idx)) buckets.set(idx, []);
    buckets.get(idx).push(row);
  });

  return Array.from(buckets.entries())
    .sort((a, b) => b[0] - a[0]) // 오래된 구간 → 최신 구간
    .map(([idx, group]) => {
      const startMs = latestMs - (idx * step + step - 1) * DAY_MS;
      const endMs = latestMs - idx * step * DAY_MS;
      const start = fmtYmd(startMs);
      const end = fmtYmd(endMs);

      const out = { fullDate: start, date: start.slice(5), rangeLabel: `${start.slice(5)} ~ ${end.slice(5)}` };
      keys.forEach((k) => {
        out[k] = average(group.map((r) => r[k]));
      });
      return out;
    });
};
