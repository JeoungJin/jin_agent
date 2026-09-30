package com.jin.gateway.service;

import com.jin.gateway.dto.ChatRequest;
import com.jin.gateway.dto.ChatResponse;
import java.time.Duration;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Flux;

/** FastAPI 에이전트 호출 담당. 장애 시 fallback으로 사용자에게 에러 대신 안내를 돌려준다. */
@Service
public class AiGatewayService {

    private static final Logger log = LoggerFactory.getLogger(AiGatewayService.class);
    private static final String DEFAULT_CUSTOMER = "C001";

    private final WebClient client;
    private final Duration timeout;

    public AiGatewayService(WebClient agentWebClient, @Value("${agent.timeout-seconds}") long timeoutSeconds) {
        this.client = agentWebClient;
        this.timeout = Duration.ofSeconds(timeoutSeconds);
    }

    public ChatResponse chat(ChatRequest req) {
        String sid = sessionId(req);
        try {
            return client.post().uri("/api/v1/chat")
                    .bodyValue(body(req))
                    .retrieve().bodyToMono(ChatResponse.class)
                    .block(timeout);
        } catch (Exception e) {
            log.warn("FastAPI 호출 실패: {}", e.toString());
            return ChatResponse.fallback(sid);
        }
    }

    public Flux<ServerSentEvent<String>> stream(ChatRequest req) {
        return client.post().uri("/api/v1/chat/stream")
                .accept(MediaType.TEXT_EVENT_STREAM)
                .bodyValue(body(req))
                .retrieve()
                .bodyToFlux(new ParameterizedTypeReference<ServerSentEvent<String>>() {})
                .timeout(timeout)
                .onErrorResume(e -> {
                    log.warn("FastAPI 스트림 실패: {}", e.toString());
                    return Flux.just(
                            ServerSentEvent.<String>builder().event("error")
                                    .data("{\"message\":\"AI 서비스에 연결할 수 없습니다.\"}").build(),
                            ServerSentEvent.<String>builder().event("done").data("{}").build());
                });
    }

    private Map<String, Object> body(ChatRequest req) {
        return Map.of("session_id", sessionId(req), "message", req.message(), "customer_id", DEFAULT_CUSTOMER);
    }

    private String sessionId(ChatRequest req) {
        return req.sessionId() == null || req.sessionId().isBlank() ? "default" : req.sessionId();
    }
}
