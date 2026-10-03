package com.jin.gateway.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/** Spring → FastAPI 요청 본문. React 가 보낸 question 에 서버가 결정한 로그인 사용자 ID(user_id)를 더한다. */
public record FastApiRouteRequest(String question, @JsonProperty("user_id") Long userId) {
}
