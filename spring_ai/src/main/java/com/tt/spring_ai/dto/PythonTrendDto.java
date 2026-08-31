package com.tt.spring_ai.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public record PythonTrendDto(
        @JsonProperty("status") String status,
        @JsonProperty("keyword_id") Long keywordId,
        @JsonProperty("keyword_name") String keywordName,
        @JsonProperty("updated_at") String updatedAt,
        @JsonProperty("trends") TrendSummary trends,
        @JsonProperty("twitter_trends") List<Object> twitterTrends,
        @JsonProperty("naver_trend") List<Object> naverTrend,
        @JsonProperty("google_trend") List<Object> googleTrend
) {
    @JsonIgnoreProperties(ignoreUnknown = true)
    public record TrendSummary(
            @JsonProperty("latest_naver_ratio") Double latestNaverRatio,
            @JsonProperty("latest_google_ratio") Double latestGoogleRatio,
            @JsonProperty("short_term_avg") Double shortTermAvg,
            @JsonProperty("long_term_avg") Double longTermAvg,
            @JsonProperty("math_prediction") String mathPrediction
    ) {}
}