package com.tt.spring_ai.dto;

import java.util.List;

public record TrendDto(
        TrendStatus trendStatus,
        String analysisReason,
        List<String> recommendedItems
) {
    public enum TrendStatus {
        RISING,
        PEAKING,
        DECLINING,
        INSUFFICIENT_DATA
    }
}