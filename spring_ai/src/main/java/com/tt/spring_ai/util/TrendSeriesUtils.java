package com.tt.spring_ai.util;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

public final class TrendSeriesUtils {

    private TrendSeriesUtils() {}

    public static List<Double> buildQuerySeries(List<Map<String, Object>> rawTrend) {
        if (rawTrend == null || rawTrend.isEmpty()) {
            return List.of();
        }

        List<Double> series = new ArrayList<>();
        for (Map<String, Object> row : sortByPeriod(rawTrend)) {
            Object raw = row.get("relative_ratio");
            if (raw instanceof Number n) {
                series.add(n.doubleValue());
            }
        }
        return series;
    }

    public static LocalDate lastDate(List<Map<String, Object>> rawTrend) {
        if (rawTrend == null || rawTrend.isEmpty()) {
            return null;
        }
        List<Map<String, Object>> sorted = sortByPeriod(rawTrend);
        Object period = sorted.get(sorted.size() - 1).get("period");
        if (period == null) {
            return null;
        }
        String text = String.valueOf(period);
        try {
            return LocalDate.parse(text.length() >= 10 ? text.substring(0, 10) : text);
        } catch (Exception e) {
            return null;
        }
    }

    private static List<Map<String, Object>> sortByPeriod(List<Map<String, Object>> rawTrend) {
        List<Map<String, Object>> sorted = new ArrayList<>(rawTrend);
        sorted.sort(Comparator.comparing(row -> String.valueOf(row.get("period"))));
        return sorted;
    }
}
