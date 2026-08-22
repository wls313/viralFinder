package com.tt.spring_ai.dto;

import java.util.List;

public record TrendDto(
        TrendStatus trendStatus,
        String analysisReason,
        List<String> recommendedItems
) {
    public enum TrendStatus {
        RISING,             // 도입/성장기
        PEAKING,            // 성숙/유지기
        DECLINING,          // 쇠퇴기
        INSUFFICIENT_DATA   // 분석 불가
    }
}