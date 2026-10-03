package com.jin.gateway.service;

import com.jin.gateway.dto.AiRouteRequest;
import com.jin.gateway.dto.AiRouteResponse;
import java.time.Duration;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

/**
 * 역할: FastAPI(POST /api/v1/chat)를 WebClient로 호출하는 서비스.
 * 응답은 JSON 한 건이므로 Mono로 받고, 실패하면 fallback 응답으로 바꿔 돌려준다.
 */
@Service
public class AiGatewayService {

    private static final Logger log = LoggerFactory.getLogger(AiGatewayService.class);
    private static final String CHAT_PATH = "/api/v1/chat";

    private final WebClient webClient;
    private final Duration timeout;

    public AiGatewayService(WebClient fastApiWebClient,
                            @Value("${fastapi.timeout-seconds}") long timeoutSeconds) {
        this.webClient = fastApiWebClient;
        this.timeout = Duration.ofSeconds(timeoutSeconds);
    }

    public Mono<AiRouteResponse> route(AiRouteRequest request) {
        return webClient.post()
                .uri(CHAT_PATH)
                .bodyValue(request)
                .retrieve()
                .bodyToMono(AiRouteResponse.class)   // 단일 응답이므로 Mono
                .timeout(timeout)                    // 3초 안에 못 받으면 TimeoutException
                .onErrorResume(e -> {                // 4xx/5xx, 연결 실패, 타임아웃 모두 여기로
                    log.error("FastAPI 호출 실패: question='{}', cause={}", request.question(), e.toString());
                    return Mono.just(AiRouteResponse.fallback(request.question()));
                });
    }
}
