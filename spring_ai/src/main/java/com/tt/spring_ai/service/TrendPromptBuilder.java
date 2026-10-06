package com.tt.spring_ai.service;

import com.tt.spring_ai.dto.CaseMatchDto;
import com.tt.spring_ai.dto.ForecastDto;
import com.tt.spring_ai.dto.PythonTrendDto;
import com.tt.spring_ai.dto.TrendDto;
import org.springframework.ai.converter.BeanOutputConverter;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.stream.Collectors;

@Component
public class TrendPromptBuilder {

    private final BeanOutputConverter<TrendDto> converter = new BeanOutputConverter<>(TrendDto.class);

    public String build(String keyword, PythonTrendDto pythonData, List<CaseMatchDto> similarCases,
                        int windowDays, ForecastDto forecast) {
        var trends = pythonData.trends();

        double naverRatio = valueOr(trends != null ? trends.latestNaverRatio() : null);
        double googleRatio = valueOr(trends != null ? trends.latestGoogleRatio() : null);
        String mathPrediction = (trends != null && trends.mathPrediction() != null) ? trends.mathPrediction() : "INSUFFICIENT_DATA";
        String naverMomentum = describeMomentum(trends != null ? trends.naver() : null);
        String googleMomentum = describeMomentum(trends != null ? trends.google() : null);
        int twitterCount = pythonData.twitterTrends() != null ? pythonData.twitterTrends().size() : 0;
        String twitterText = twitterCount > 0
                ? twitterCount + "건"
                : "수집된 데이터 없음 (수집에 실패했을 수 있으니 소셜 미디어 언급이 적다고 해석하지 마세요)";

        String caseSection = similarCases.isEmpty()
                ? "참고할 만한 과거 유사 사례가 아직 없습니다."
                : similarCases.stream()
                    .map(c -> String.format("- '%s' (결과: %s): %s", c.keyword(), outcomeLabel(c.outcome()), c.summaryText()))
                    .collect(Collectors.joining("\n"));

        String forecastSection = describeForecast(forecast);

        return String.format("""
            당신은 시계열 데이터와 과거 유사 사례를 근거로 '트렌드의 남은 수명'을 예측하는 트렌드 애널리스트입니다.
            아래 데이터를 바탕으로 '%s'의 현재 트렌드 수명 단계와 상세 분석을 작성하세요.

            [현재 데이터]
            - 네이버/구글 검색 지수: %.1f / %.1f
            - 규칙 기반 통계 판정(math_prediction): %s (코드가 이미 계산한 값입니다. 근거 없이 뒤집지 말고 이 판정을 우선 반영해서 해석하세요)
            - 네이버 모멘텀: %s
            - 구글 모멘텀: %s
            - 최근 X(트위터) 언급 샘플: %s

            [과거 유사 사례 - 지금과 비슷한 %d일 구간의 모양을 보였던 키워드들의 실제 결과]
            %s

            [예측 요약 - 화면의 예측 그래프(앞으로 3개월)에 그대로 표시되는 값]
            %s

            [분석 및 예측 가이드라인]
            1. trendStatus 판별: RISING, PEAKING, DECLINING, STEADY, INSUFFICIENT_DATA 중 택 1
               (math_prediction, 유사 사례 결과, 예측 요약의 흐름을 함께 고려해서 판단하세요)
               - 예측 요약에서 '꾸준한 상품'으로 판정됐다면 STEADY를 고르세요.
            2. analysisReason 작성 규칙 (중요):
               - 이 글은 통계/마케팅 지식이 전혀 없는 일반인이 읽습니다.
               - "모멘텀", "이동평균", "통계 판정", "math_prediction" 같은 내부 용어나 영어 코드명을 절대 그대로 쓰지 마세요.
               - 대신 "최근 N일간 검색량이 꾸준히 늘고 있어요", "비슷했던 과거 사례들은 보통 이렇게 됐어요" 처럼
                 누구나 바로 이해할 수 있는 쉬운 일상 문장으로 풀어서 설명하세요.
               - 수치를 언급할 때도 "지수 72"처럼 날것으로 던지지 말고, "평소보다 훨씬 많이 검색되고 있어요" 같이
                 의미를 해석해서 전달하세요.
               - 유사 사례를 인용할 때는 실제 키워드명과 그 결과를 자연스러운 문장으로 녹여서 설명하세요
                 (예: "두바이초콜릿처럼 꾸준히 인기를 유지한 사례와 비슷한 흐름이에요").
            3. 예측 요약과의 일관성 (중요):
               - 위 [예측 요약]의 수치와 방향은 화면 그래프에 그대로 표시됩니다. 설명이 이와 어긋나면 안 됩니다.
               - 예측 요약에 없는 미래 수치(예: 6개월 뒤, 1년 뒤 수치)를 새로 지어내지 마세요.
               - 예측 요약의 배수는 '최근 1주 평균' 대비입니다. '약 2.8배'를 '280퍼센트 더 많이'처럼 바꿔 쓰지 말고,
                 '약 2.8배', '절반 정도'처럼 그대로 전달하세요.
               - 예측 정점이 있으면 반드시 언급하세요. 정점이 준비 기간(약 3개월)보다 먼저 오면,
                 지금 준비를 시작해도 문을 열 때는 정점이 이미 지나 있을 가능성이 높다는 점을 분명히 알려주세요.
               - '꾸준한 상품' 판정은 최근 약 3개월 데이터만 보고 내린 것입니다. 그 이전에 크게 유행했다가 식은 상품일 수도 있으므로,
                 "이미 대중에게 자리 잡은 상품", "장기적으로 안정적인 수요" 처럼 오랜 기간에 대한 판단은 하지 마세요.
                 대신 "최근 몇 달 동안은 검색량이 큰 변화 없이 비슷하게 유지되고 있어요"처럼 기간을 분명히 밝혀서 설명하세요.
               - 읽는 사람은 창업을 고민하는 사람입니다. 준비 기간(약 3개월)을 고려해
                 지금 시작해도 괜찮은 시점인지 한두 문장으로 조언을 덧붙이세요.

            [출력 주의사항]
            - 마크다운, 백틱, 부가 텍스트 없이 오직 유효한 단일 JSON 객체({ ... })만 출력하십시오.

            %s
            """,
                keyword, naverRatio, googleRatio, mathPrediction, naverMomentum, googleMomentum,
                twitterText, windowDays, caseSection, forecastSection, converter.getFormat());
    }

    private String describeForecast(ForecastDto f) {
        if (f == null) {
            return "데이터가 부족해 예측 그래프를 만들지 못했습니다. 미래 수치를 지어내지 말고, 데이터가 부족하다는 점을 설명하세요.";
        }

        StringBuilder sb = new StringBuilder();
        if (f.steady()) {
            sb.append("- 판정: 꾸준한 상품 (최근 약 3개월 동안 검색량이 거의 일정함, 그 이전 흐름은 반영되지 않음)\n");
        }
        for (ForecastDto.Milestone m : f.milestones()) {
            sb.append(String.format("- %d개월 뒤: 최근 1주 평균의 약 %.1f배 (%s)%n", m.months(), m.percentOfNow() / 100.0, m.status()));
        }
        if (f.peakInDays() != null) {
            sb.append(String.format("- 예측 정점: 약 %d일 뒤, 최근 1주 평균의 약 %.1f배까지 오른 뒤 내려감%n",
                    f.peakInDays(), f.peakTimesNow()));
        }
        if (f.outcomeShare() != null && !f.outcomeShare().isEmpty()) {
            String share = f.outcomeShare().entrySet().stream()
                    .map(e -> String.format("%s %.0f%%", outcomeLabel(e.getKey()), e.getValue() * 100))
                    .collect(Collectors.joining(", "));
            sb.append(String.format("- 예측에 참고한 비슷한 사례 %d개의 결과 비율: %s%n", f.basedOnCases(), share));
        }
        sb.append("- 화면 결론 문구: ").append(f.headline());
        return sb.toString();
    }

    private String outcomeLabel(String code) {
        if (code == null) return "알 수 없음";
        return switch (code) {
            case "FADED" -> "인기가 식은 사례";
            case "SUSTAINED" -> "인기를 유지한 사례";
            case "REIGNITED" -> "다시 인기를 얻은 사례";
            case "STEADY" -> "꾸준히 검색되는 사례";
            default -> code;
        };
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
