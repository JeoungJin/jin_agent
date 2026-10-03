package com.jin.gateway.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/**
 * 역할: React → Spring, 그리고 Spring → FastAPI 요청 본문.
 * FastAPI의 QuestionRequest(question)와 JSON 필드명이 같아야 한다.
 */
public record AiRouteRequest(@NotBlank @Size(max = 2000) String question) {
}
