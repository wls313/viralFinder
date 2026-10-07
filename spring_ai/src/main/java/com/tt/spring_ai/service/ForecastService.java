package com.tt.spring_ai.service;

import com.tt.spring_ai.dto.ForecastDto;
import com.tt.spring_ai.service.CaseSimilarityService.CaseWindowMatch;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class ForecastService {

    public static final int WINDOW_DAYS = 90;     // 비교에 쓰는 최근 기간
    public static final int FORECAST_DAYS = 90;   // 예측 기간 (3개월)

    private static final int ANCHOR_DAYS = 7;            // "현재 값" = 최근 7일 평균 (하루 튀는 값 무시)
    private static final double MIN_LEVEL = 1.0;         // 이보다 낮으면 검색이 거의 없는 것으로 보고 예측 안 함
    private static final double STEADY_MAX_CV = 0.10;    // 변동폭(표준편차/평균) 10% 이하면 평평
    private static final double STEADY_MAX_SHIFT = 0.10; // 앞 1/3 평균 대비 뒤 1/3 평균 변화가 10% 이하면 평평
    private static final double MIN_CASE_ANCHOR = 0.5;   // 사례 쪽 기준값이 너무 작으면 비율이 폭주해서 제외
    private static final double MAX_RATIO = 5.0;         // 사례가 몇 배로 뛰었는지 상한 (튀는 사례 하나가 끌고 가는 것 방지)
    private static final int SMOOTH_DAYS = 7;            // 예측선을 7일 이동평균으로 부드럽게
    private static final double PEAK_MIN_RATIO = 1.10;
    private static final double PEAK_DROP_RATIO = 0.85;

    public static List<Double> recentWindow(List<Double> series) {
        if (series == null || series.isEmpty()) {
            return List.of();
        }
        int from = Math.max(0, series.size() - WINDOW_DAYS);
        return List.copyOf(series.subList(from, series.size()));
    }

    public ForecastDto forecast(List<Double> window, LocalDate lastDate, List<CaseWindowMatch> matches) {
        if (window == null || window.size() < CaseSimilarityService.MIN_WINDOW_DAYS) {
            return null;
        }
        LocalDate baseDate = lastDate != null ? lastDate : LocalDate.now();

        double anchor = mean(window, window.size() - ANCHOR_DAYS, window.size());
        double lastValue = window.get(window.size() - 1);
        if (anchor < MIN_LEVEL) {
            return null;
        }

        if (isSteady(window)) {
            double[] flat = new double[FORECAST_DAYS + 1];
            Arrays.fill(flat, anchor);
            flat[0] = lastValue;
            double[] center = smooth(flat);
            center[0] = lastValue;
            return build(true, center, anchor, baseDate, Map.of(), 0);
        }

        if (matches == null || matches.isEmpty()) {
            return null;
        }

        double[] weightedSum = new double[FORECAST_DAYS + 1];
        double weightTotal = 0.0;
        Map<String, Double> outcomeWeight = new HashMap<>();
        int used = 0;

        for (CaseWindowMatch m : matches) {
            List<Double> s = m.series();
            int end = m.windowEnd();
            if (end + FORECAST_DAYS > s.size()) {
                continue;
            }
            double caseAnchor = mean(s, end - ANCHOR_DAYS, end);
            if (caseAnchor < MIN_CASE_ANCHOR) {
                continue;
            }

            double weight = 1.0 / (m.distance() + 0.02);
            for (int d = 1; d <= FORECAST_DAYS; d++) {
                double ratio = Math.min(s.get(end - 1 + d) / caseAnchor, MAX_RATIO);
                weightedSum[d] += weight * ratio;
            }
            weightTotal += weight;
            outcomeWeight.merge(m.trendCase().getOutcome(), weight, Double::sum);
            used++;
        }

        if (used == 0) {
            return null;
        }

        double[] raw = new double[FORECAST_DAYS + 1];
        raw[0] = lastValue;
        for (int d = 1; d <= FORECAST_DAYS; d++) {
            raw[d] = anchor * weightedSum[d] / weightTotal;
        }
        double[] center = smooth(raw);
        center[0] = lastValue;

        Map<String, Double> share = new LinkedHashMap<>();
        double total = weightTotal;
        outcomeWeight.entrySet().stream()
                .sorted(Map.Entry.<String, Double>comparingByValue().reversed())
                .forEach(e -> share.put(e.getKey(), Math.round(e.getValue() / total * 1000) / 1000.0));

        return build(false, center, anchor, baseDate, share, used);
    }

    private ForecastDto build(boolean steady, double[] center, double anchor, LocalDate baseDate,
                              Map<String, Double> outcomeShare, int basedOnCases) {
        List<ForecastDto.Point> points = new ArrayList<>();
        for (int d = 0; d <= FORECAST_DAYS; d++) {
            points.add(new ForecastDto.Point(baseDate.plusDays(d), round2(Math.max(center[d], 0.0))));
        }

        List<ForecastDto.Milestone> milestones = new ArrayList<>();
        for (int months : new int[]{1, 3}) {
            int day = Math.min(months * 30, FORECAST_DAYS);
            double value = Math.max(center[day], 0.0);
            double percent = value / anchor * 100.0;
            milestones.add(new ForecastDto.Milestone(months, baseDate.plusDays(day), round2(value),
                    Math.round(percent * 10) / 10.0, steady ? "유지" : statusOf(percent)));
        }

        Integer peakInDays = null;
        Double peakTimesNow = null;
        if (!steady) {
            int peakDay = 1;
            for (int d = 2; d <= FORECAST_DAYS; d++) {
                if (center[d] > center[peakDay]) {
                    peakDay = d;
                }
            }
            double peakRatio = center[peakDay] / anchor;
            if (peakRatio >= PEAK_MIN_RATIO && peakDay < FORECAST_DAYS - 7
                    && center[FORECAST_DAYS] <= center[peakDay] * PEAK_DROP_RATIO) {
                peakInDays = peakDay;
                peakTimesNow = Math.round(peakRatio * 10) / 10.0;
            }
        }

        String headline;
        if (steady) {
            headline = "꾸준히 검색되는 상품이에요. 앞으로도 비슷한 수준이 이어질 가능성이 높아요";
        } else if (peakInDays != null) {
            headline = whenText(peakInDays) + " 정점을 찍고 내려올 가능성이 높아요";
        } else {
            headline = headlineOf(milestones.get(milestones.size() - 1).status());
        }

        return new ForecastDto(steady, headline, round2(anchor), points, milestones, outcomeShare, basedOnCases,
                peakInDays, peakTimesNow);
    }

    private String whenText(int days) {
        if (days < 14) {
            return "약 " + days + "일 뒤";
        }
        return "약 " + Math.round(days / 7.0) + "주 뒤";
    }

    /** 최근 구간이 평평한지: 변동폭이 작고, 앞부분 대비 뒷부분 수준 변화도 작아야 함 */
    private boolean isSteady(List<Double> window) {
        int n = window.size();
        double mean = mean(window, 0, n);
        if (mean <= 0) {
            return false;
        }
        double[] raw = new double[n];
        for (int i = 0; i < n; i++) {
            raw[i] = window.get(i);
        }
        double var = 0.0;
        for (double v : smooth(raw)) {
            var += (v - mean) * (v - mean);
        }
        double cv = Math.sqrt(var / n) / mean;

        int third = n / 3;
        double head = mean(window, 0, third);
        double tail = mean(window, n - third, n);
        double shift = head > 0 ? Math.abs(tail / head - 1.0) : Double.MAX_VALUE;

        return cv <= STEADY_MAX_CV && shift <= STEADY_MAX_SHIFT;
    }

    private String statusOf(double percentOfNow) {
        if (percentOfNow >= 110) return "상승";
        if (percentOfNow >= 90) return "유지";
        if (percentOfNow >= 50) return "하락";
        return "급락";
    }

    private String headlineOf(String status) {
        return switch (status) {
            case "상승" -> "앞으로 더 많이 검색될 가능성이 높아요";
            case "유지" -> "지금 수준을 유지할 가능성이 높아요";
            case "하락" -> "하락 구간에 들어섰을 가능성이 높아요";
            default -> "관심이 빠르게 식을 가능성이 높아요";
        };
    }

    private double[] smooth(double[] values) {
        int half = SMOOTH_DAYS / 2;
        double[] out = new double[values.length];
        for (int i = 0; i < values.length; i++) {
            int from = Math.max(0, i - half);
            int to = Math.min(values.length - 1, i + half);
            double sum = 0.0;
            for (int j = from; j <= to; j++) {
                sum += values[j];
            }
            out[i] = sum / (to - from + 1);
        }
        return out;
    }

    private static double mean(List<Double> values, int from, int to) {
        from = Math.max(0, from);
        to = Math.min(values.size(), to);
        if (to <= from) {
            return 0.0;
        }
        double sum = 0.0;
        for (int i = from; i < to; i++) {
            sum += values.get(i);
        }
        return sum / (to - from);
    }

    private static double round2(double v) {
        return Math.round(v * 100) / 100.0;
    }
}
