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
        factory.setConnectTimeout((int) Duration.ofSeconds(5).toMillis());
        factory.setReadTimeout((int) Duration.ofSeconds(15).toMillis());

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

        double naverRatio = (pythonData.trends() != null) ? pythonData.trends().latest_naver_ratio() : 0.0;
        double googleRatio = (pythonData.trends() != null) ? pythonData.trends().latest_google_ratio() : 0.0;
        int twitterCount = (pythonData.twitter_trends() != null) ? pythonData.twitter_trends().size() : 0;

        double shortTermAvg = (pythonData.trends() != null) ? pythonData.trends().short_term_avg() : 0.0;
        double longTermAvg = (pythonData.trends() != null) ? pythonData.trends().long_term_avg() : 0.0;
        String mathPrediction = (pythonData.trends() != null) ? pythonData.trends().math_prediction() : "STAY";

        BeanOutputConverter<TrendDto> converter =
                new BeanOutputConverter<>(TrendDto.class);

        String prompt = String.format("""
            당신은 데이터 시계열 패턴을 분석하여 '트렌드의 남은 수명'을 예측하고, '제2의 유행 아이템'을 발굴하는 트렌드 애널리스트입니다.
            주어진 데이터 지표를 바탕으로 '%s'의 현재 트렌드 수명 단계와 차세대 추천 아이템을 분석하세요.
            
            [데이터 요약]
            - 현재 네이버/구글 검색 지수: %.1f / %.1f
            - 최근 확산 중인 X(트위터) 주요 언급량: %d건
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
               
            3. recommendedItems (제2의 발굴 아이템):
               - '%s'가 초기(도입기)에 그렸던 상승 그래프 패턴과 유사하게, **현재 막 주목받기 시작한 동종 업계/유사 카테고리의 신흥 아이템 2가지**를 발굴해서 추천하세요.
               - 이미 정점을 찍은 유명한 아이템은 제외하고, 이제 막 그래프가 꿈틀대는 '얼리 어답터' 성향의 아이템이어야 합니다.
            
            %s
            """, keyword, naverRatio, googleRatio, twitterCount, shortTermAvg, longTermAvg, keyword, converter.getFormat());

        String aiResponseText = chatClient.prompt()
                .user(prompt)
                .call()
                .content();

        return converter.convert(aiResponseText);
    }
}