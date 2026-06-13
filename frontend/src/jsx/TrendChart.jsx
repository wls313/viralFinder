import { useState } from 'react';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';

import '../css/chart.css';

function TrendChart({result}) {
  const [platform, setPlatform] = useState('all');

  const naverData = 
    result?.naver_trend?.map((item) => ({
      date: item.period.slice(5),
      count: item.ratio,
    })) || [];

  const chartData = {
    all: [
      { date: '05/01', count: 120 },
      { date: '05/02', count: 180 },
      { date: '05/03', count: 260 },
      { date: '05/04', count: 1200 },
      { date: '05/05', count: 3400 },
      { date: '05/06', count: 5200 },
      { date: '05/07', count: 4300 },
    ],

    x: [
      { date: '05/01', count: 80 },
      { date: '05/02', count: 120 },
      { date: '05/03', count: 210 },
      { date: '05/04', count: 900 },
      { date: '05/05', count: 2600 },
      { date: '05/06', count: 4100 },
      { date: '05/07', count: 3700 },
    ],

    instagram: [
      { date: '05/01', count: 30 },
      { date: '05/02', count: 50 },
      { date: '05/03', count: 90 },
      { date: '05/04', count: 220 },
      { date: '05/05', count: 480 },
      { date: '05/06', count: 720 },
      { date: '05/07', count: 650 },
    ],

    naver: naverData,
  };

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h3>채널별 언급량 추이</h3>

        <div className="platform-list">
          <button
            onClick={() => setPlatform('all')}
            className={
              platform === 'all'
                ? 'active'
                : ''
            }
          >
            전체
          </button>

          <button
            onClick={() => setPlatform('x')}
            className={
              platform === 'x'
                ? 'active'
                : ''
            }
          >
            X
          </button>

          <button
            onClick={() =>
              setPlatform('instagram')
            }
            className={
              platform === 'instagram'
                ? 'active'
                : ''
            }
          >
            인스타
          </button>

          <button
            onClick={() => setPlatform('naver')}
            className={
              platform === 'naver'
                ? 'active'
                : ''
            }
          >
            네이버
          </button>
        </div>
      </div>

      <div className="chart-wrapper">
        <ResponsiveContainer
          width="100%"
          height={400}
        >
          <LineChart
            data={chartData[platform]}
          >
            <CartesianGrid
              strokeDasharray="3 3"
            />

            <XAxis dataKey="date" />

            <YAxis />

            <Tooltip />

            <Line
              type="monotone"
              dataKey="count"
              stroke="#4f46e5"
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