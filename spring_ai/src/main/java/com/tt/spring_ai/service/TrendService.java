package com.tt.spring_ai.service;

import com.tt.spring_ai.dto.PythonTrendDto;
import com.tt.spring_ai.dto.TrendDto;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.converter.BeanOutputConverter;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.time.Duration;

@Service
public class TrendService {

    private final RestClient restClient;
    private final ChatClient chatClient;
    private final BeanOutputConverter<TrendDto> converter;

    public TrendService(ChatClient.Builder chatClientBuilder) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setReadTimeout((int) Duration.ofSeconds(180).toMillis());

        this.restClient = RestClient.builder()
                .baseUrl("http://localhost:8000")
                .requestFactory(factory)
                .build();

        this.chatClient = chatClientBuilder.build();
        this.converter = new BeanOutputConverter<>(TrendDto.class);
    }

    public TrendDto trendRecommend(String keyword) {
        PythonTrendDto pythonData = trendFetchData(keyword);

        String prompt = trendBuildPrompt(keyword, pythonData);

        return trendCallAiAndParse(prompt);
    }

    private PythonTrendDto trendFetchData(String keyword) {
        PythonTrendDto pythonData = restClient.get()
                .uri("/api/analysis/{keyword}", keyword)
                .retrieve()
                .body(PythonTrendDto.class);

        if (pythonData == null || !"success".equals(pythonData.status())) {
            throw new RuntimeException("트렌드 데이터를 수집하지 못했습니다.");
        }
        return pythonData;
    }

    private String trendBuildPrompt(String keyword, PythonTrendDto pythonData) {
        double naverRatio = (pythonData.trends() != null && pythonData.trends().latestNaverRatio() != null)
                ? pythonData.trends().latestNaverRatio() : 0.0;
        double googleRatio = (pythonData.trends() != null && pythonData.trends().latestGoogleRatio() != null)
                ? pythonData.trends().latestGoogleRatio() : 0.0;
        int twitterCount = (pythonData.twitterTrends() != null)
                ? pythonData.twitterTrends().size() : 0;
        double shortTermAvg = (pythonData.trends() != null && pythonData.trends().shortTermAvg() != null)
                ? pythonData.trends().shortTermAvg() : 0.0;
        double longTermAvg = (pythonData.trends() != null && pythonData.trends().longTermAvg() != null)
                ? pythonData.trends().longTermAvg() : 0.0;

        return String.format("""
            당신은 데이터 시계열 패턴을 분석하여 '트렌드의 남은 수명'을 예측하는 트렌드 애널리스트입니다.
            주어진 데이터 지표를 바탕으로 '%s'의 현재 트렌드 수명 단계와 상세 분석을 작성하세요.
            
            [데이터 요약]
            - 현재 네이버/구글 검색 지수: %.1f / %.1f
            - 최근 확산 중인 X(트위터) 주요 언급 샘플: %d건
            - 네이버 검색 지수 단기 평균(최근 3일): %.1f
            - 네이버 검색 지수 장기 평균(최근 14일): %.1f
            
            [분석 및 예측 가이드라인]
            1. trendStatus 판별: RISING, PEAKING, DECLINING, INSUFFICIENT_DATA 중 택 1
            2. analysisReason: 수치를 인용하여 수명 주기 단계와 지속 기간 예측 설명
            
            [출력 주의사항]
            - 마크다운, 백틱, 부가 텍스트 없이 오직 유효한 단일 JSON 객체({ ... })만 출력하십시오.
            
            %s
            """, keyword, naverRatio, googleRatio, twitterCount, shortTermAvg, longTermAvg, converter.getFormat());
    }

    private TrendDto trendCallAiAndParse(String prompt) {
        String aiResponseText = chatClient.prompt()
                .user(prompt)
                .call()
                .content();

        String cleanJson = aiResponseText;
        if (cleanJson != null) {
            int startIndex = cleanJson.indexOf("{");
            int endIndex = cleanJson.lastIndexOf("}");
            if (startIndex != -1 && endIndex != -1 && endIndex >= startIndex) {
                cleanJson = cleanJson.substring(startIndex, endIndex + 1);
            }
        }
        return converter.convert(cleanJson);
    }
}