package com.tt.spring_ai.dto;

import java.util.List;

public record PythonTrendDto(
        String status,
        Long keyword_id,
        String keyword_name,
        String updated_at,
        TrendSummary trends,
        List<Object> twitter_trends
) {
    public record TrendSummary(
            double latest_naver_ratio,
            double latest_google_ratio,
            double short_term_avg,
            double long_term_avg,
            String math_prediction
    ) {}
}