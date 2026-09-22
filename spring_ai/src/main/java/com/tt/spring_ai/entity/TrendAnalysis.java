package com.tt.spring_ai.entity;

import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "trend_analysis")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Builder
public class TrendAnalysis {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "analysis_id")
    private Long analysisId;

    @Column(name = "keyword_id", nullable = false)
    private Long keywordId;

    @Column(name = "keyword_name", nullable = false, length = 100)
    private String keywordName;

    @Builder.Default
    @Column(name = "analyzed_at", nullable = false)
    private LocalDateTime analyzedAt = LocalDateTime.now();

    @Column(name = "latest_naver_ratio", precision = 5, scale = 2)
    private BigDecimal latestNaverRatio;

    @Column(name = "latest_google_ratio", precision = 5, scale = 2)
    private BigDecimal latestGoogleRatio;

    @Column(name = "naver_short_term_avg", precision = 5, scale = 2)
    private BigDecimal naverShortTermAvg;

    @Column(name = "naver_long_term_avg", precision = 5, scale = 2)
    private BigDecimal naverLongTermAvg;

    @Column(name = "math_prediction", length = 20)
    private String mathPrediction;

    @Column(name = "matched_case_ids", columnDefinition = "JSON")
    private String matchedCaseIds;

    // ---- LLM 결과 ----
    @Column(name = "trend_status", nullable = false, length = 20)
    private String trendStatus;

    @Lob
    @Column(name = "analysis_reason")
    private String analysisReason;

    @Column(name = "recommended_items", columnDefinition = "JSON")
    private String recommendedItems;

    @Column(name = "model_name", length = 50)
    private String modelName;

    @Column(name = "prompt_version", length = 20)
    private String promptVersion;

    // ---- 사후 검증용 (나중에 배치나 수동으로 채움) ----
    @Column(name = "actual_outcome", length = 20)
    private String actualOutcome;

    @Column(name = "verified_at")
    private LocalDateTime verifiedAt;
}
