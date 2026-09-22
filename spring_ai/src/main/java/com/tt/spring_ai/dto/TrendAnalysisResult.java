package com.tt.spring_ai.dto;

import java.util.List;

public record TrendAnalysisResult(
        TrendDto aiAnalysis,
        String mathPrediction,
        List<CaseMatchDto> similarCases
) {}
