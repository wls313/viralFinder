import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';

import '../css/chart.css';

// 8월 22일 ~ 9월 21일 (1달 기준, 탕후루 급등-급락 트렌드) 더미데이터
const DUMMY_TREND_DATA = [
  { date: '08-22', naver: 10, google: 6, x: 12 },
  { date: '08-24', naver: 18, google: 12, x: 25 },
  { date: '08-26', naver: 35, google: 24, x: 48 },
  { date: '08-28', naver: 58, google: 42, x: 72 },
  { date: '08-30', naver: 85, google: 68, x: 90 },
  { date: '09-01', naver: 100, google: 92, x: 100 }, // 정점 (Peak)
  { date: '09-03', naver: 88, google: 84, x: 80 },
  { date: '09-05', naver: 70, google: 72, x: 58 },
  { date: '09-07', naver: 52, google: 58, x: 38 },
  { date: '09-09', naver: 38, google: 45, x: 24 },
  { date: '09-11', naver: 25, google: 32, x: 14 },
  { date: '09-13', naver: 16, google: 22, x: 8 },
  { date: '09-15', naver: 10, google: 15, x: 4 },
  { date: '09-17', naver: 7, google: 10, x: 2 },
  { date: '09-19', naver: 5, google: 7, x: 1 },
  { date: '09-21', naver: 4, google: 5, x: 0 }, // 마지막 날짜 (9월 21일)
];

function TrendChart({ result }) {
  console.log("result: ", result);

  const naverData =
    result?.naver_trend?.map((item) => ({
      date: item.period.slice(5),
      count: item.relative_ratio,
    })) || [];

  const googleData =
    result?.google_trend?.map((item) => ({
      date: item.period.slice(5),
      count: item.relative_ratio,
    })) || [];

  const xData =
    result?.x_trend?.map((item) => ({
      date: item.period.slice(5),
      count: item.ratio,
    })) || [];

  const mergeData = [];

  const mergeInto = (data, key) => {
    data.forEach((item) => {
      const existing = mergeData.find((d) => d.date === item.date);

      if (existing) {
        existing[key] = item.count;
      } else {
        mergeData.push({
          date: item.date,
          naver: null,
          google: null,
          x: null,
          [key]: item.count,
        });
      }
    });
  };

  mergeInto(naverData, "naver");
  mergeInto(googleData, "google");
  mergeInto(xData, "x");

  mergeData.sort((a, b) => a.date.localeCompare(b.date));

  // 전달받은 데이터가 없으면 1달 기준 더미데이터 사용
  const chartData = mergeData.length > 0 ? mergeData : DUMMY_TREND_DATA;
  const isDummy = mergeData.length === 0;

  return (
    <div className="chart-card">
      <div className="chart-header" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <h3>트렌드 검색량 변화</h3>
        {isDummy && (
          <span
            style={{
              backgroundColor: '#f3f4f6',
              color: '#6b7280',
              fontSize: '11px',
              fontWeight: 500,
              padding: '3px 8px',
              borderRadius: '6px',
            }}
          >
            예시 데이터 (탕후루)
          </span>
        )}
      </div>

      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />

            <XAxis dataKey="date" />

            <YAxis />

            <Tooltip />

            <Legend />

            <Line
              type="monotone"
              dataKey="naver"
              name="네이버"
              stroke="#03C75A"
              strokeWidth={3}
              dot={{ r: 4 }}
              connectNulls
            />

            <Line
              type="monotone"
              dataKey="google"
              name="구글"
              stroke="#4285F4"
              strokeWidth={3}
              dot={{ r: 4 }}
              connectNulls
            />

            {/* <Line
              type="monotone"
              dataKey="x"
              name="X (트위터)"
              stroke="#14171A"
              strokeWidth={3}
              dot={{ r: 4 }}
              connectNulls
            /> */}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default TrendChart;