package com.tt.spring_ai.service;

import com.tt.spring_ai.dto.TrendDto;
import com.tt.spring_ai.dto.PythonTrendDto;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.converter.BeanOutputConverter;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

@Service
public class TrendService {

    private final RestClient restClient;
    private final ChatClient chatClient;

    public TrendService(ChatClient.Builder chatClientBuilder) {
        this.restClient = RestClient.builder()
                .baseUrl("http://localhost:8000")
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

        double naverRatio = pythonData.trends().latest_naver_ratio();
        double googleRatio = pythonData.trends().latest_google_ratio();
        int twitterCount = (pythonData.twitter_trends() != null) ? pythonData.twitter_trends().size() : 0;

        BeanOutputConverter<TrendDto> converter =
                new BeanOutputConverter<>(TrendDto.class);

        String prompt = String.format("""
            당신은 트렌드 분석 전문가입니다. 다음 수집된 데이터를 바탕으로 '%s'의 유행 상태를 분석해주세요.
            
            [데이터 요약]
            - 네이버 검색 지속 지수 (0~100): %.1f
            - 구글 검색 지속 지수 (0~100): %.1f
            - 최근 확산 중인 X(트위터) 주요 언급량: %d건
            
            [분석 가이드라인]
            1. STEADY_TREND: 네이버 또는 구글 검색 지수가 15점 이상으로 꾸준히 유지되거나, 장기적인 소비 흐름이 관측되는 경우 (트위터 언급량이 적더라도 포털 검색이 유지되면 지속 트렌드로 판단 가능).
            2. SHORT_TERM_VIRAL: 검색 지수는 낮거나 급락하는 추세인데, 트위터 언급량만 일시적으로 폭증한 경우(반짝 바이럴/밈).
            3. INSUFFICIENT_DATA: 네이버/구글 검색 지수가 모두 5점 미만으로 극히 낮고, 트위터 언급량도 거의 없어 분석 자체가 불가능한 경우.
            4. 해당 아이템과 연관되거나 대체 가능한 추천 상품을 2가지 제시하세요.
            
            %s
            """, keyword, naverRatio, googleRatio, twitterCount, converter.getFormat());

        String aiResponseText = chatClient.prompt()
                .user(prompt)
                .call()
                .content();

        return converter.convert(aiResponseText);
    }
}