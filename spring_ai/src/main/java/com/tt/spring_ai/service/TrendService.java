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
        // 1. 파이썬 FastAPI 서버 호출
        PythonTrendDto pythonData = restClient.get()
                .uri("/api/analysis/{keyword}", keyword)
                .retrieve()
                .body(PythonTrendDto.class);

        if (pythonData == null || !"success".equals(pythonData.status())) {
            throw new RuntimeException("트렌드 데이터를 수집하지 못했습니다.");
        }

        // 2. 데이터 추출
        double naverRatio = pythonData.trends().latest_naver_ratio();
        double googleRatio = pythonData.trends().latest_google_ratio();
        int twitterCount = (pythonData.twitter_trends() != null) ? pythonData.twitter_trends().size() : 0;

        // 3. Converter 세팅
        BeanOutputConverter<TrendDto> converter =
                new BeanOutputConverter<>(TrendDto.class);

        // 4. 프롬프트 작성
        String prompt = String.format("""
            당신은 트렌드 분석 전문가입니다. 다음 수집된 데이터를 바탕으로 '%s'의 유행 상태를 분석해주세요.
            
            [데이터 요약]
            - 네이버 검색 지속 지수 (0~100): %.1f
            - 구글 검색 지속 지수 (0~100): %.1f
            - 최근 확산 중인 X(트위터) 주요 언급량: %d건
            
            [분석 가이드라인]
            1. 트위터 언급량은 많은데 검색 지수가 낮으면 'SHORT_TERM_VIRAL'로 판단하세요.
            2. 검색 지수가 꾸준히 높거나 상승세라면 'STEADY_TREND'로 판단하세요.
            3. 트위터와 검색 지수 모두 현저히 낮다면 'INSUFFICIENT_DATA'로 판단하세요.
            4. 해당 아이템과 비슷한 흐름으로 떠오르고 있는 대체 상품이나 연관 상품을 2가지 추천해주세요.
            
            %s
            """, keyword, naverRatio, googleRatio, twitterCount, converter.getFormat());

        // 5. AI 호출 및 결과 반환
        String aiResponseText = chatClient.prompt()
                .user(prompt)
                .call()
                .content();

        return converter.convert(aiResponseText);
    }
}