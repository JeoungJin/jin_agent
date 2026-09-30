package com.jin.gateway.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/** React → Spring 요청. customerId는 원래 로그인 세션(JWT)에서 꺼내지만 수업에서는 고정값을 쓴다. */
public record ChatRequest(
        String sessionId,
        @NotBlank @Size(max = 2000) String message) {
}
