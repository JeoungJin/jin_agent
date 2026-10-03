package com.jin.gateway.service;

import com.jin.gateway.dto.AiRouteRequest;
import com.jin.gateway.dto.AiRouteResponse;
import java.time.Duration;
import java.util.concurrent.TimeoutException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientRequestException;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Mono;

/**
 * 역할: FastAPI(POST /api/v1/route)를 WebClient로 호출하는 서비스.
 * 응답은 JSON 한 건이므로 Mono로 받는다.
 * 타임아웃 · 연결 거부 · FastAPI 5xx 일 때만 fallback(HTTP 200 + category FALLBACK)으로 바꾸고,
 * 4xx(요청 자체가 잘못됨)는 fallback 하지 않고 그대로 에러로 전파한다.
 */
@Service
public class AiGatewayService {

    private static final Logger log = LoggerFactory.getLogger(AiGatewayService.class);
    private static final String ROUTE_PATH = "/api/v1/route";

    private final WebClient webClient;
    private final Duration timeout;

    public AiGatewayService(WebClient fastApiWebClient, @Value("${ai.fastapi.timeout}") Duration timeout) {
        this.webClient = fastApiWebClient;
        this.timeout = timeout;
    }

    public Mono<AiRouteResponse> route(AiRouteRequest request) {
        return webClient.post()
                .uri(ROUTE_PATH)
                .bodyValue(request)
                .retrieve()
                .bodyToMono(AiRouteResponse.class)
                .timeout(timeout)
                .onErrorResume(AiGatewayService::isFallbackTarget, e -> {
                    log.warn("FastAPI 호출 실패 → fallback: type={}, message={}, question='{}'",
                            e.getClass().getSimpleName(), e.getMessage(), request.question());
                    return Mono.just(AiRouteResponse.fallback(request.question()));
                });
    }

    /** fallback 대상: 타임아웃, 연결 거부(요청 자체가 못 나감), FastAPI 5xx. 4xx 는 대상이 아니다. */
    static boolean isFallbackTarget(Throwable e) {
        if (e instanceof TimeoutException || e instanceof WebClientRequestException) {
            return true;
        }
        return e instanceof WebClientResponseException r && r.getStatusCode().is5xxServerError();
    }
}
