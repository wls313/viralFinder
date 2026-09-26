package com.tt.spring_ai.util;

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

        List<Map<String, Object>> sorted = new ArrayList<>(rawTrend);
        sorted.sort(Comparator.comparing(row -> String.valueOf(row.get("period"))));

        List<Double> series = new ArrayList<>();
        for (Map<String, Object> row : sorted) {
            Object raw = row.get("relative_ratio");
            if (raw instanceof Number n) {
                series.add(n.doubleValue());
            }
        }
        return series;
    }
}
