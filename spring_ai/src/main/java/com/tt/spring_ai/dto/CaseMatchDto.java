package com.tt.spring_ai.dto;

public record CaseMatchDto(
        Long caseId,
        String keyword,
        String outcome,
        String summaryText,
        double distance
) {}
