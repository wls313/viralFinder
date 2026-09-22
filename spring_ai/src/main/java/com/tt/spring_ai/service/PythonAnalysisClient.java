package com.tt.spring_ai.service;

import com.tt.spring_ai.dto.PythonTrendDto;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.time.Duration;

@Component
public class PythonAnalysisClient {

    private final RestClient restClient;

    public PythonAnalysisClient(@Value("${python.service.base-url}") String baseUrl) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setReadTimeout((int) Duration.ofSeconds(180).toMillis());

        this.restClient = RestClient.builder()
                .baseUrl(baseUrl)
                .requestFactory(factory)
                .build();
    }

    public PythonTrendDto fetchAnalysis(String keyword, String period) {
        PythonTrendDto data = restClient.get()
                .uri(uriBuilder -> uriBuilder
                        .path("/api/analysis/{keyword}")
                        .queryParam("period", period)
                        .build(keyword))
                .retrieve()
                .body(PythonTrendDto.class);

        if (data == null || !"success".equals(data.status())) {
            throw new IllegalStateException("파이썬 서버에서 '" + keyword + "' 트렌드 데이터를 가져오지 못했습니다.");
        }
        return data;
    }
}
