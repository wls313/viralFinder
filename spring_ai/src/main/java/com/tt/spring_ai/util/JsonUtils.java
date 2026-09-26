package com.tt.spring_ai.util;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.Collections;
import java.util.List;

public final class JsonUtils {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    private JsonUtils() {}

    /** 객체를 JSON 문자열로 변환 */
    public static String toJson(Object value) {
        if (value == null) {
            return null;
        }
        try {
            return MAPPER.writeValueAsString(value);
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("JSON 직렬화 실패: " + e.getMessage(), e);
        }
    }

    /** JSON 문자열을 List&lt;T&gt;로 변환 */
    public static <T> List<T> fromJsonList(String json, Class<T> elementType) {
        if (json == null || json.isBlank()) {
            return Collections.emptyList();
        }
        try {
            return MAPPER.readValue(
                    json,
                    MAPPER.getTypeFactory().constructCollectionType(List.class, elementType)
            );
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("JSON 역직렬화 실패: " + e.getMessage(), e);
        }
    }

    /** JSON 문자열을 임의 타입으로 변환 (필요 시 사용) */
    public static <T> T fromJson(String json, Class<T> type) {
        if (json == null || json.isBlank()) {
            return null;
        }
        try {
            return MAPPER.readValue(json, type);
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("JSON 역직렬화 실패: " + e.getMessage(), e);
        }
    }

    /** TypeReference 기반 변환 (제네릭 타입용) */
    public static <T> T fromJson(String json, TypeReference<T> typeRef) {
        if (json == null || json.isBlank()) {
            return null;
        }
        try {
            return MAPPER.readValue(json, typeRef);
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("JSON 역직렬화 실패: " + e.getMessage(), e);
        }
    }
}