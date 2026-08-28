package com.tt.spring_ai.service;

import com.tt.spring_ai.dto.TrendDto;
import com.tt.spring_ai.dto.PythonTrendDto;
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

    public TrendService(ChatClient.Builder chatClientBuilder) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setReadTimeout((int) Duration.ofSeconds(180).toMillis());

        this.restClient = RestClient.builder()
                .baseUrl("http://localhost:8000")
                .requestFactory(factory)
                .build();

        this.chatClient = chatClientBuilder.build();
    }

    public TrendDto trendRecommend(String keyword) {
        PythonTrendDto pythonData = restClient.get()
                .uri("/api/analysis/{keyword}", keyword)
                .retrieve()
                .body(PythonTrendDto.class);

        if (pythonData == null || !"success".equals(pythonData.status())) {
            throw new RuntimeException("트렌드 데이터를 수집하지 못했습니다.");
        }

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

        BeanOutputConverter<TrendDto> converter =
                new BeanOutputConverter<>(TrendDto.class);

        String prompt = String.format("""
            당신은 데이터 시계열 패턴을 분석하여 '트렌드의 남은 수명'을 예측하는 트렌드 애널리스트입니다.
            주어진 데이터 지표를 바탕으로 '%s'의 현재 트렌드 수명 단계와 상세 분석을 작성하세요.
            
            [데이터 요약]
            - 현재 네이버/구글 검색 지수: %.1f / %.1f
            - 최근 확산 중인 X(트위터) 주요 언급 샘플: %d건
            - 네이버 검색 지수 단기 평균(최근 3일): %.1f
            - 네이버 검색 지수 장기 평균(최근 14일): %.1f
            
            [분석 및 예측 가이드라인 (반드시 준수할 것)]
            1. trendStatus 판별 (수명 주기 기반):
               - RISING (도입/성장기): 단기 평균이 장기 평균을 돌파하며 가파르게 오르고 있는 상태 (앞으로의 지속 기간이 길 것으로 예상)
               - PEAKING (성숙/유지기): 단기/장기 평균이 모두 높은 수준에서 비슷하게 유지되는 상태 (당분간 트렌드 유지)
               - DECLINING (쇠퇴기): 단기 평균이 장기 평균 아래로 꺾이며 하락하는 상태 (수명이 끝나가는 중)
               - INSUFFICIENT_DATA: 데이터가 극히 적어 판단 불가
               
            2. analysisReason (수명 및 지속 기간 예측):
               - 주어진 수치(단기/장기 평균 등)를 반드시 인용하여 현재 이 아이템이 트렌드 수명 주기 중 어느 단계인지 설명하세요.
               - 앞으로 이 유행이 어느 정도(예: 단기적, 수개월 지속 등) 더 유지될 수 있을지 타당한 근거를 들어 예측하세요.

            [출력 주의사항]
            - 마크다운 헤더(###), 백틱(```), 설명 문장, 인사말 등 부가 텍스트를 일절 출력하지 마십시오.
            - 오직 유효한 단일 JSON 객체({ ... }) 형식으로만 출력하십시오.
            
            %s
            """, keyword, naverRatio, googleRatio, twitterCount, shortTermAvg, longTermAvg, converter.getFormat());

        String aiResponseText = chatClient.prompt()
                .user(prompt)
                .call()
                .content();

        System.out.println("=== AI 응답 원문 ===");
        System.out.println(aiResponseText);
        System.out.println("===================");

        String cleanJson = aiResponseText;
        if (cleanJson != null) {
            int startIndex = cleanJson.indexOf("{");
            int endIndex = cleanJson.lastIndexOf("}");
            if (startIndex != -1 && endIndex != -1 && endIndex >= startIndex) {
                cleanJson = cleanJson.substring(startIndex, endIndex + 1);
            }
        }

        // 3. 파싱 및 반환
        return converter.convert(cleanJson);
    }
}