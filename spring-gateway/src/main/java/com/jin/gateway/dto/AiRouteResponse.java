package com.jin.gateway.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

/**
 * 역할: FastAPI의 AnswerResponse(question, answer, category)를 받아 React로 돌려주는 응답.
 * FastAPI가 필드를 더 추가해도 깨지지 않도록 모르는 필드는 무시한다.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public record AiRouteResponse(String question, String answer, String category) {

    public static final String FALLBACK_CATEGORY = "FALLBACK";
    public static final String FALLBACK_MESSAGE = "현재 AI 서비스가 원활하지 않습니다. 잠시 후 다시 시도해주세요";

    /** FastAPI 호출 실패 시 사용자에게 돌려줄 대체 응답. 정상 응답과 구분되도록 category 는 FALLBACK. */
    public static AiRouteResponse fallback(String question) {
        return new AiRouteResponse(question, FALLBACK_MESSAGE, FALLBACK_CATEGORY);
    }
}
