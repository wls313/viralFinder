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

    private final TrendCaseRepository trendCaseRepository;

    public CaseSimilarityService(TrendCaseRepository trendCaseRepository) {
        this.trendCaseRepository = trendCaseRepository;
    }

    public List<CaseMatchDto> findSimilarCases(List<Double> querySeries, int topK) {
        if (querySeries == null || querySeries.isEmpty()) {
            return List.of();
        }

        int windowSize = querySeries.size();
        List<CaseMatchDto> scored = new ArrayList<>();

        for (TrendCase c : trendCaseRepository.findAll()) {
            List<SeriesPointDto> series = JsonUtils.fromJsonList(c.getSeriesJson(), SeriesPointDto.class);
            if (series.size() < windowSize) {
                continue;
            }

            List<Double> caseWindow = series.subList(0, windowSize).stream()
                    .map(SeriesPointDto::ratio)
                    .toList();

            double distance = euclideanDistance(querySeries, caseWindow);
            scored.add(new CaseMatchDto(c.getCaseId(), c.getKeyword(), c.getOutcome(), c.getSummaryText(), distance));
        }

        return scored.stream()
                .sorted(Comparator.comparingDouble(CaseMatchDto::distance))
                .limit(topK)
                .toList();
    }

    private double euclideanDistance(List<Double> a, List<Double> b) {
        double sum = 0.0;
        for (int i = 0; i < a.size(); i++) {
            double diff = a.get(i) - b.get(i);
            sum += diff * diff;
        }
        return Math.sqrt(sum);
    }
}
