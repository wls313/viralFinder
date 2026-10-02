package com.tt.spring_ai.service;

import com.tt.spring_ai.dto.CaseMatchDto;
import com.tt.spring_ai.dto.PythonTrendDto;
import com.tt.spring_ai.dto.TrendDto;
import org.springframework.ai.converter.BeanOutputConverter;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.stream.Collectors;

@Component
public class TrendPromptBuilder {

    private final BeanOutputConverter<TrendDto> converter = new BeanOutputConverter<>(TrendDto.class);

    public String build(String keyword, PythonTrendDto pythonData, List<CaseMatchDto> similarCases, int windowDays) {
        var trends = pythonData.trends();

        double naverRatio = valueOr(trends != null ? trends.latestNaverRatio() : null);
        double googleRatio = valueOr(trends != null ? trends.latestGoogleRatio() : null);
        String mathPrediction = (trends != null && trends.mathPrediction() != null) ? trends.mathPrediction() : "INSUFFICIENT_DATA";
        String naverMomentum = describeMomentum(trends != null ? trends.naver() : null);
        String googleMomentum = describeMomentum(trends != null ? trends.google() : null);
        int twitterCount = pythonData.twitterTrends() != null ? pythonData.twitterTrends().size() : 0;

        String caseSection = similarCases.isEmpty()
                ? "참고할 만한 과거 유사 사례가 아직 없습니다."
                : similarCases.stream()
                    .map(c -> String.format("- '%s' (결과: %s): %s", c.keyword(), c.outcome(), c.summaryText()))
                    .collect(Collectors.joining("\n"));

        return String.format("""
            당신은 시계열 데이터와 과거 유사 사례를 근거로 '트렌드의 남은 수명'을 예측하는 트렌드 애널리스트입니다.
            아래 데이터를 바탕으로 '%s'의 현재 트렌드 수명 단계와 상세 분석을 작성하세요.

            [현재 데이터]
            - 네이버/구글 검색 지수: %.1f / %.1f
            - 규칙 기반 통계 판정(math_prediction): %s (코드가 이미 계산한 값입니다. 근거 없이 뒤집지 말고 이 판정을 우선 반영해서 해석하세요)
            - 네이버 모멘텀: %s
            - 구글 모멘텀: %s
            - 최근 X(트위터) 언급 샘플: %d건

            [과거 유사 사례 - 지금과 비슷한 초반 %d일 구간의 모양을 보였던 키워드들의 실제 결과]
            %s

            [분석 및 예측 가이드라인]
            1. trendStatus 판별: RISING, PEAKING, DECLINING, INSUFFICIENT_DATA 중 택 1
               (math_prediction과 위 유사 사례의 결과를 함께 고려해서 판단하세요)
            2. analysisReason 작성 규칙 (중요):
               - 이 글은 통계/마케팅 지식이 전혀 없는 일반인이 읽습니다.
               - "모멘텀", "이동평균", "통계 판정", "math_prediction" 같은 내부 용어나 영어 코드명을 절대 그대로 쓰지 마세요.
               - 대신 "최근 N일간 검색량이 꾸준히 늘고 있어요", "비슷했던 과거 사례들은 보통 이렇게 됐어요" 처럼
                 누구나 바로 이해할 수 있는 쉬운 일상 문장으로 풀어서 설명하세요.
               - 수치를 언급할 때도 "지수 72"처럼 날것으로 던지지 말고, "평소보다 훨씬 많이 검색되고 있어요" 같이
                 의미를 해석해서 전달하세요.
               - 유사 사례를 인용할 때는 실제 키워드명과 그 결과를 자연스러운 문장으로 녹여서 설명하세요
                 (예: "두바이초콜릿처럼 꾸준히 인기를 유지한 사례와 비슷한 흐름이에요").

            [출력 주의사항]
            - 마크다운, 백틱, 부가 텍스트 없이 오직 유효한 단일 JSON 객체({ ... })만 출력하십시오.

            %s
            """,
                keyword, naverRatio, googleRatio, mathPrediction, naverMomentum, googleMomentum,
                twitterCount, windowDays, caseSection, converter.getFormat());
    }

    private String describeMomentum(PythonTrendDto.TrendSummary.MomentumResult m) {
        if (m == null || m.prediction() == null) return "데이터 부족";
        return String.format("%s (단기평균 %.1f / 장기평균 %.1f)",
                m.prediction(), valueOr(m.shortTermAvg()), valueOr(m.longTermAvg()));
    }

    private double valueOr(Double v) {
        return v != null ? v : 0.0;
    }

    public BeanOutputConverter<TrendDto> converter() {
        return converter;
    }
}
