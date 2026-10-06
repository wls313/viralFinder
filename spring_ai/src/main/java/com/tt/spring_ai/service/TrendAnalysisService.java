package com.tt.spring_ai.service;

import com.tt.spring_ai.dto.CaseMatchDto;
import com.tt.spring_ai.dto.ForecastDto;
import com.tt.spring_ai.dto.PythonTrendDto;
import com.tt.spring_ai.dto.TrendAnalysisResult;
import com.tt.spring_ai.dto.TrendDto;
import com.tt.spring_ai.entity.TrendAnalysis;
import com.tt.spring_ai.repository.TrendAnalysisRepository;
import com.tt.spring_ai.service.CaseSimilarityService.CaseWindowMatch;
import com.tt.spring_ai.util.JsonUtils;
import com.tt.spring_ai.util.TrendSeriesUtils;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

@Service
public class TrendAnalysisService {

    private static final int TOP_K_CASES = 3;        // 화면/프롬프트에 보여줄 유사 사례 수
    private static final int FORECAST_CASES = 25;    // 예측선 계산에 참고할 유사 사례 수
    private static final String MODEL_NAME = "gemini-2.5-flash";
    private static final String PROMPT_VERSION = "v3-forecast";

    private final PythonAnalysisClient pythonAnalysisClient;
    private final CaseSimilarityService caseSimilarityService;
    private final ForecastService forecastService;
    private final TrendPromptBuilder promptBuilder;
    private final TrendAnalysisRepository trendAnalysisRepository;
    private final ChatClient chatClient;

    public TrendAnalysisService(PythonAnalysisClient pythonAnalysisClient,
                                 CaseSimilarityService caseSimilarityService,
                                 ForecastService forecastService,
                                 TrendPromptBuilder promptBuilder,
                                 TrendAnalysisRepository trendAnalysisRepository,
                                 ChatClient.Builder chatClientBuilder) {
        this.pythonAnalysisClient = pythonAnalysisClient;
        this.caseSimilarityService = caseSimilarityService;
        this.forecastService = forecastService;
        this.promptBuilder = promptBuilder;
        this.trendAnalysisRepository = trendAnalysisRepository;
        this.chatClient = chatClientBuilder.build();
    }

    public TrendAnalysisResult analyze(String keyword, String period) {
        PythonTrendDto pythonData = pythonAnalysisClient.fetchAnalysis(keyword, period);

        List<Double> querySeries = TrendSeriesUtils.buildQuerySeries(pythonData.naverTrend());
        List<Double> window = ForecastService.recentWindow(querySeries);
        LocalDate lastDate = TrendSeriesUtils.lastDate(pythonData.naverTrend());

        List<CaseWindowMatch> matches =
                caseSimilarityService.findBestWindows(window, FORECAST_CASES, ForecastService.FORECAST_DAYS);
        List<CaseMatchDto> similarCases = matches.isEmpty()
                ? caseSimilarityService.findSimilarCases(window, TOP_K_CASES)
                : caseSimilarityService.toDisplay(matches, TOP_K_CASES);

        ForecastDto forecast = forecastService.forecast(window, lastDate, matches);

        String prompt = promptBuilder.build(keyword, pythonData, similarCases, window.size(), forecast);
        TrendDto aiResult = callAiAndParse(prompt);

        String mathPrediction = (pythonData.trends() != null && pythonData.trends().mathPrediction() != null)
                ? pythonData.trends().mathPrediction() : "INSUFFICIENT_DATA";

        saveAnalysisLog(pythonData, similarCases, aiResult, mathPrediction);

        return new TrendAnalysisResult(aiResult, mathPrediction, similarCases, forecast);
    }

    private TrendDto callAiAndParse(String prompt) {
        String aiResponseText = chatClient.prompt().user(prompt).call().content();

        String cleanJson = aiResponseText;
        if (cleanJson != null) {
            int start = cleanJson.indexOf("{");
            int end = cleanJson.lastIndexOf("}");
            if (start != -1 && end != -1 && end >= start) {
                cleanJson = cleanJson.substring(start, end + 1);
            }
        }
        return promptBuilder.converter().convert(cleanJson);
    }

    private void saveAnalysisLog(PythonTrendDto pythonData, List<CaseMatchDto> similarCases,
                                  TrendDto aiResult, String mathPrediction) {
        try {
            var trends = pythonData.trends();
            var naverMomentum = trends != null ? trends.naver() : null;

            TrendAnalysis log = TrendAnalysis.builder()
                    .keywordId(pythonData.keywordId())
                    .keywordName(pythonData.keywordName())
                    .analyzedAt(LocalDateTime.now())
                    .latestNaverRatio(toBigDecimal(trends != null ? trends.latestNaverRatio() : null))
                    .latestGoogleRatio(toBigDecimal(trends != null ? trends.latestGoogleRatio() : null))
                    .naverShortTermAvg(toBigDecimal(naverMomentum != null ? naverMomentum.shortTermAvg() : null))
                    .naverLongTermAvg(toBigDecimal(naverMomentum != null ? naverMomentum.longTermAvg() : null))
                    .mathPrediction(mathPrediction)
                    .matchedCaseIds(JsonUtils.toJson(similarCases.stream().map(CaseMatchDto::caseId).toList()))
                    .trendStatus(aiResult.trendStatus().name())
                    .analysisReason(aiResult.analysisReason())
                    .recommendedItems(JsonUtils.toJson(aiResult.recommendedItems()))
                    .modelName(MODEL_NAME)
                    .promptVersion(PROMPT_VERSION)
                    .build();

            trendAnalysisRepository.save(log);
        } catch (Exception e) {
            System.err.println("[TrendAnalysisService] 분석 로그 저장 실패: " + e.getMessage());
        }
    }

    private BigDecimal toBigDecimal(Double value) {
        return value == null ? null : BigDecimal.valueOf(value);
    }
}
