package com.tt.spring_ai.service;

import com.tt.spring_ai.dto.CaseMatchDto;
import com.tt.spring_ai.dto.SeriesPointDto;
import com.tt.spring_ai.entity.TrendCase;
import com.tt.spring_ai.repository.TrendCaseRepository;
import com.tt.spring_ai.util.JsonUtils;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

@Service
public class CaseSimilarityService {

    public static final int MIN_WINDOW_DAYS = 28;
    private static final double MIN_ACTIVE_RATIO = 0.3;

    private final TrendCaseRepository trendCaseRepository;

    public CaseSimilarityService(TrendCaseRepository trendCaseRepository) {
        this.trendCaseRepository = trendCaseRepository;
    }

    public record CaseWindowMatch(TrendCase trendCase, List<Double> series, int offset, int windowSize, double distance) {
        public int windowEnd() {
            return offset + windowSize;
        }
    }

    public List<CaseMatchDto> findSimilarCases(List<Double> querySeries, int topK) {
        return toDisplay(findBestWindows(querySeries, topK, 0), topK);
    }

    public List<CaseWindowMatch> findBestWindows(List<Double> querySeries, int topK, int requiredFutureDays) {
        if (querySeries == null || querySeries.size() < MIN_WINDOW_DAYS) {
            return List.of();
        }
        double[] query = normalizeByMax(querySeries, 0, querySeries.size());
        if (query == null) {
            return List.of();
        }
        int windowSize = query.length;

        List<CaseWindowMatch> matches = new ArrayList<>();
        for (TrendCase c : trendCaseRepository.findAll()) {
            List<Double> series = JsonUtils.fromJsonList(c.getSeriesJson(), SeriesPointDto.class).stream()
                    .map(SeriesPointDto::ratio)
                    .toList();

            int lastOffset = series.size() - windowSize - requiredFutureDays;
            if (lastOffset < 0) {
                continue;
            }

            double caseMax = series.stream().mapToDouble(Double::doubleValue).max().orElse(0.0);
            double minWindowMax = caseMax * MIN_ACTIVE_RATIO;

            double bestDistance = Double.MAX_VALUE;
            int bestOffset = -1;
            for (int offset = 0; offset <= lastOffset; offset++) {
                double d = windowDistance(query, series, offset, minWindowMax);
                if (d < bestDistance) {
                    bestDistance = d;
                    bestOffset = offset;
                }
            }
            if (bestOffset >= 0 && bestDistance < Double.MAX_VALUE) {
                matches.add(new CaseWindowMatch(c, series, bestOffset, windowSize, bestDistance));
            }
        }

        return matches.stream()
                .sorted(Comparator.comparingDouble(CaseWindowMatch::distance))
                .limit(topK)
                .toList();
    }

    public List<CaseMatchDto> toDisplay(List<CaseWindowMatch> matches, int topK) {
        return matches.stream()
                .limit(topK)
                .map(m -> new CaseMatchDto(
                        m.trendCase().getCaseId(),
                        m.trendCase().getKeyword(),
                        m.trendCase().getOutcome(),
                        m.trendCase().getSummaryText(),
                        Math.round(m.distance() * 1000) / 1000.0))
                .toList();
    }

    private double windowDistance(double[] query, List<Double> series, int offset, double minWindowMax) {
        int n = query.length;
        double max = 0.0;
        for (int i = 0; i < n; i++) {
            max = Math.max(max, series.get(offset + i));
        }
        if (max <= 0.0 || max < minWindowMax) {
            return Double.MAX_VALUE;
        }
        double sum = 0.0;
        for (int i = 0; i < n; i++) {
            double diff = query[i] - series.get(offset + i) / max;
            sum += diff * diff;
        }
        return Math.sqrt(sum / n);
    }

    private double[] normalizeByMax(List<Double> values, int from, int to) {
        double max = 0.0;
        for (int i = from; i < to; i++) {
            max = Math.max(max, values.get(i));
        }
        if (max <= 0.0) {
            return null;
        }
        double[] out = new double[to - from];
        for (int i = from; i < to; i++) {
            out[i - from] = values.get(i) / max;
        }
        return out;
    }
}
