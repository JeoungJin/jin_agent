package com.jin.gateway.error;

import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import org.springframework.web.server.ResponseStatusException;

/** 에러 응답을 {"status": 코드, "message": 문구} 한 가지 형식으로 통일한다. */
@RestControllerAdvice
public class GlobalExceptionHandler {

    /** @Valid 검증 실패 (null · 빈 문자열 · 공백 질문) → FastAPI 를 호출하기 전에 400 */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, Object>> handleValidation(MethodArgumentNotValidException e) {
        String message = e.getBindingResult().getFieldErrors().stream()
                .findFirst().map(f -> f.getDefaultMessage()).orElse("요청 형식이 올바르지 않습니다");
        return body(HttpStatus.BAD_REQUEST, message);
    }

    /** 본문이 없거나 JSON 이 깨진 경우 */
    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<Map<String, Object>> handleUnreadable(HttpMessageNotReadableException e) {
        return body(HttpStatus.BAD_REQUEST, "요청 형식이 올바르지 않습니다");
    }

    /** FastAPI 4xx: fallback 하지 않고 같은 상태코드로 전달한다. (5xx 는 서비스에서 이미 fallback 처리됨) */
    @ExceptionHandler(WebClientResponseException.class)
    public ResponseEntity<Map<String, Object>> handleUpstream(WebClientResponseException e) {
        HttpStatusCode status = e.getStatusCode();
        String message = status.value() == 422 ? "요청 형식이 올바르지 않습니다" : "요청을 처리할 수 없습니다";
        return ResponseEntity.status(status).body(Map.of("status", status.value(), "message", message));
    }

    /** 403 · 404 처럼 코드에서 직접 던진 상태 예외 */
    @ExceptionHandler(ResponseStatusException.class)
    public ResponseEntity<Map<String, Object>> handleStatus(ResponseStatusException e) {
        HttpStatusCode status = e.getStatusCode();
        String message = e.getReason() != null ? e.getReason() : "요청을 처리할 수 없습니다";
        return ResponseEntity.status(status).body(Map.of("status", status.value(), "message", message));
    }

    private ResponseEntity<Map<String, Object>> body(HttpStatus status, String message) {
        return ResponseEntity.status(status).body(Map.of("status", status.value(), "message", message));
    }
}
