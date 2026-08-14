package com.tt.spring_ai.dto;

import java.util.List;

public record TrendDto(
        TrendStatus trendStatus,
        String analysisReason,
        List<String> recommendedItems
) {
    public enum TrendStatus {
        SHORT_TERM_VIRAL,   // 단기 바이럴
        STEADY_TREND,       // 지속 트렌드
        INSUFFICIENT_DATA   // 데이터 부족
    }
}