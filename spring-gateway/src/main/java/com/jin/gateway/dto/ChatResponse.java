package com.jin.gateway.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
import java.util.Map;

@JsonIgnoreProperties(ignoreUnknown = true)
public record ChatResponse(
        @JsonProperty("session_id") String sessionId,
        String answer,
        List<Step> steps) {

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record Step(String tool, Map<String, Object> arguments, Map<String, Object> result) {
    }

    public static ChatResponse fallback(String sessionId) {
        return new ChatResponse(sessionId, "AI 상담 서비스가 일시적으로 응답하지 않습니다. 잠시 후 다시 시도해 주세요.", List.of());
    }
}
