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

// X(트위터) 데이터: 아직 백엔드에 X API 연동이 안 되어 있어서
// result.x_trend가 없거나 빈 배열일 수 있음. 그 경우 그래프에서
// 해당 라인은 그냥 표시되지 않음(에러 없이 안전하게 처리).
function TrendChart({result}) {
  const naverData = 
    result?.naver_trend?.map((item) => ({
      date: item.period.slice(5),
      count: item.ratio,
    })) || [];

  const googleData =
  result?.google_trend?.map(item => ({
    date: item.period.slice(5),
    count: item.ratio
  })) || [];

  const xData =
    result?.x_trend?.map(item => ({
      date: item.period.slice(5),
      count: item.ratio
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

  mergeData.sort((a, b) =>
    a.date.localeCompare(b.date)
  );

  const hasAnyData = mergeData.length > 0;

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h3>트렌드 검색량 변화</h3>

      </div>

      <div className="chart-wrapper">
        {hasAnyData ? (
          <ResponsiveContainer
            width="100%"
            height={400}
          >
            <LineChart
              data={mergeData}
            >
              <CartesianGrid
                strokeDasharray="3 3"
              />

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

              <Line
                type="monotone"
                dataKey="x"
                name="X (트위터)"
                stroke="#14171A"
                strokeWidth={3}
                dot={{ r: 4 }}
                connectNulls
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p className="chart-empty">아직 표시할 트렌드 데이터가 없습니다.</p>
        )}
      </div>
    </div>
  );
}

export default TrendChart;
