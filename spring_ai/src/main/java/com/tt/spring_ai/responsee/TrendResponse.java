package com.tt.spring_ai.responsee;

import java.util.List;
import java.util.Map;

public record TrendResponse(
        String status,
        Long keyword_id,
        String keyword_name,
        String updated_at,
        TrendData trends,
        List<Map<String, Object>> twitter_trends
) {
    public record TrendData(
            double latest_naver_ratio,
            double latest_google_ratio,
            List<Map<String, Object>> raw_data_preview
    ) {}
}