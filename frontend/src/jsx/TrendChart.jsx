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

  const mergeData = [];

  naverData.forEach((item) => {
    const existing = mergeData.find(
      (d) => d.date === item.date
    );

    if (existing) {
      existing.naver = item.count;
    } else {
      mergeData.push({
        date: item.date,
        naver: item.count,
        google: null,
      });
    }
  });

  googleData.forEach((item) => {
    const existing = mergeData.find(
      (d) => d.date === item.date
    );

    if (existing) {
      existing.google = item.count;
    } else {
      mergeData.push({
        date: item.date,
        google: item.count,
        naver: null,
      });
    }
  });

  mergeData.sort((a, b) =>
    a.date.localeCompare(b.date)
  );

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h3>트렌드 검색량 변화</h3>

      </div>

      <div className="chart-wrapper">
        <ResponsiveContainer
            width="100%"
            height={320}
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
            />

            <Line
              type="monotone"
              dataKey="google"
              name="구글"
              stroke="#4285F4"
              strokeWidth={3}
              dot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default TrendChart;