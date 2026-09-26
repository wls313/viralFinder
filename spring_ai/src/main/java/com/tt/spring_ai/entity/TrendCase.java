package com.tt.spring_ai.entity;

import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Entity
@Table(name = "trend_case")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Builder
public class TrendCase {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "case_id")
    private Long caseId;

    @Column(nullable = false, length = 100)
    private String keyword;

    @Column(name = "period_start", nullable = false)
    private LocalDate periodStart;

    @Column(name = "period_end", nullable = false)
    private LocalDate periodEnd;

    @Lob
    @Column(name = "series_json", nullable = false, columnDefinition = "JSON")
    private String seriesJson;

    @Column(name = "days_to_peak", nullable = false)
    private Integer daysToPeak;

    @Column(name = "peak_ratio", precision = 5, scale = 2, nullable = false)
    private BigDecimal peakRatio;

    @Column(name = "ratio_28d_after_peak", precision = 5, scale = 2, nullable = false)
    private BigDecimal ratio28dAfterPeak;

    @Column(precision = 6, scale = 3, nullable = false)
    private BigDecimal volatility;

    @Column(nullable = false, length = 20)
    private String outcome;

    @Column(name = "summary_text", length = 500, nullable = false)
    private String summaryText;

    @Builder.Default
    @Column(name = "created_at")
    private LocalDateTime createdAt = LocalDateTime.now();
}
