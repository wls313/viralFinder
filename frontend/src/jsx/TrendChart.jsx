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

function TrendChart({result}) {
  console.log("result: ", result)

  const naverData =
    result?.naver_trend?.map((item) => ({
      date: item.period.slice(5),
      count: item.relative_ratio,
    })) || [];

  const googleData =
  result?.google_trend?.map(item => ({
    date: item.period.slice(5),
    count: item.relative_ratio
  })) || [];

  const xData =
    result?.x_trend?.map(item => ({
      date: item.period.slice(5),
      count: item.ratio
    })) || [];

    console.log("naverData: ", naverData)
    console.log("googleData: ", googleData)

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
