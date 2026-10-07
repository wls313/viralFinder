package com.tt.spring_ai.dto;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

public record ForecastDto(
        boolean steady,
        String headline,
        double currentLevel,
        List<Point> center,
        List<Milestone> milestones,
        Map<String, Double> outcomeShare,
        int basedOnCases,
        Integer peakInDays,
        Double peakTimesNow
) {
    public record Point(LocalDate date, double value) {}

    public record Milestone(int months, LocalDate date, double value, double percentOfNow, String status) {}
}
