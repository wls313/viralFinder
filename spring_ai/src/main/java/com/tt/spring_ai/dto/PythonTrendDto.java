package com.tt.spring_ai.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;
import java.util.Map;

@JsonIgnoreProperties(ignoreUnknown = true)
public record PythonTrendDto(
        @JsonProperty("status") String status,
        @JsonProperty("keyword_id") Long keywordId,
        @JsonProperty("keyword_name") String keywordName,
        @JsonProperty("updated_at") String updatedAt,
        @JsonProperty("trends") TrendSummary trends,
        @JsonProperty("twitter_trends") List<Object> twitterTrends,
        @JsonProperty("naver_trend") List<Map<String, Object>> naverTrend,
        @JsonProperty("google_trend") List<Map<String, Object>> googleTrend
) {
    // analyzer.py가 naver/google을 각각 독립 판정해서 내려주는 새 구조에 맞춘 형태
    @JsonIgnoreProperties(ignoreUnknown = true)
    public record TrendSummary(
            @JsonProperty("latest_naver_ratio") Double latestNaverRatio,
            @JsonProperty("latest_google_ratio") Double latestGoogleRatio,
            @JsonProperty("naver") MomentumResult naver,
            @JsonProperty("google") MomentumResult google,
            @JsonProperty("math_prediction") String mathPrediction
    ) {
        @JsonIgnoreProperties(ignoreUnknown = true)
        public record MomentumResult(
                @JsonProperty("short_term_avg") Double shortTermAvg,
                @JsonProperty("long_term_avg") Double longTermAvg,
                @JsonProperty("prediction") String prediction
        ) {}
    }
}
