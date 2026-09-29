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
import { sliceTrendByPeriod, bucketRows } from '../api/dummySearch';
import PeriodSelector from './PeriodSelector';

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

function TrendChart({ result, period = "1w", setPeriod }) {
  // 선택한 기간(7/30/90일)만 사용. period가 바뀌면 차트 데이터도 함께 바뀜.
  const naverSeries = sliceTrendByPeriod(result?.naver_trend, period);
  const googleSeries = sliceTrendByPeriod(result?.google_trend, period);
  const xSeries = sliceTrendByPeriod(
    result?.x_trend?.map((item) => ({ period: item.period, relative_ratio: item.ratio })),
    period
  );

  // 연도가 바뀌는 구간에서도 정렬이 깨지지 않도록 전체 날짜(YYYY-MM-DD)를 키로 병합하고,
  // 화면에는 MM-DD만 표시한다.
  const mergeMap = new Map();

  const mergeInto = (series, key) => {
    series.forEach((item) => {
      const fullDate = String(item.period);
      const existing = mergeMap.get(fullDate) || {
        fullDate,
        date: fullDate.slice(5),
        naver: null,
        google: null,
        x: null,
      };
      existing[key] = item.relative_ratio;
      mergeMap.set(fullDate, existing);
    });
  };

  mergeInto(naverSeries, "naver");
  mergeInto(googleSeries, "google");
  mergeInto(xSeries, "x");

  const dailyData = Array.from(mergeMap.values()).sort((a, b) =>
    a.fullDate.localeCompare(b.fullDate)
  );

  // 7일=하루 단위, 30일=3일 단위, 90일=10일 단위 평균으로 묶어서 표시
  const mergeData = bucketRows(dailyData, period);

  // 검색 결과 자체가 없을 때(검색 전 상태)만 예시 데이터 사용.
  // 검색 결과가 있는데 시계열이 비어 있으면 빈 차트 + 안내 문구를 보여줌.
  const isDummy = !result;
  const chartData = isDummy ? DUMMY_TREND_DATA : mergeData;
  const isEmpty = !isDummy && mergeData.length === 0;

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
        {result?._dummy && (
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
            더미 데이터
          </span>
        )}

        {setPeriod && (
          <div style={{ marginLeft: 'auto' }}>
            <PeriodSelector period={period} setPeriod={setPeriod} />
          </div>
        )}
      </div>

      <div className="chart-wrapper">
        {isEmpty && <p>선택한 기간에 표시할 데이터가 없습니다.</p>}
        <ResponsiveContainer width="100%" height={400}>
          <LineChart key={period} data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />

            <XAxis dataKey="date" />

            <YAxis />

            <Tooltip
              labelFormatter={(label, payload) =>
                payload?.[0]?.payload?.rangeLabel || label
              }
            />

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