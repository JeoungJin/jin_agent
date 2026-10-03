package com.jin.gateway.service;

import com.jin.gateway.dto.AiRouteRequest;
import com.jin.gateway.dto.FastApiRouteRequest;
import com.jin.gateway.dto.StockQuote;
import com.jin.gateway.security.AuthUser;
import java.time.Duration;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * 역할: FastAPI(POST /api/v1/route)의 SSE 스트림을 받아 React 로 그대로 중계한다.
 * 이벤트를 모으지 않고(collectList · block 없음) 받는 즉시 흘려보낸다. event 이름과 data 는 수정하지 않는다.
 * FastAPI 4xx 는 fallback 없이 상태코드 그대로 전파하고, 그 밖의 실패는 error 이벤트 1개로 알리고 종료한다. (done 은 보내지 않는다)
 */
@Service
public class AiGatewayService {

    private static final Logger log = LoggerFactory.getLogger(AiGatewayService.class);
    private static final String ROUTE_PATH = "/api/v1/route";
    static final String ERROR_DATA = "{\"message\":\"현재 AI 서비스가 원활하지 않습니다. 잠시 후 다시 시도해주세요\"}";

    private final WebClient webClient;
    private final Duration timeout;

    public AiGatewayService(WebClient fastApiWebClient, @Value("${ai.fastapi.timeout}") Duration timeout) {
        this.webClient = fastApiWebClient;
        this.timeout = timeout;
    }

    public Flux<ServerSentEvent<String>> route(AiRouteRequest request, AuthUser user, String accessToken) {
        return webClient.post()
                .uri(ROUTE_PATH)
                .accept(MediaType.TEXT_EVENT_STREAM)
                .headers(h -> {
                    if (accessToken != null) {
                        h.set(HttpHeaders.AUTHORIZATION, "Bearer " + accessToken);
                    }
                })
                .bodyValue(new FastApiRouteRequest(request.question(), user == null ? null : user.id()))
                .retrieve()
                .bodyToFlux(new ParameterizedTypeReference<ServerSentEvent<String>>() {})
                .timeout(timeout)      // 스트리밍에서는 전체 시간이 아니라 "이벤트와 이벤트 사이의 최대 대기시간"
                .onErrorResume(AiGatewayService::isFallbackTarget, e -> {
                    log.warn("FastAPI 스트림 실패 → error 이벤트: type={}, message={}, question='{}'",
                            e.getClass().getSimpleName(), e.getMessage(), request.question());
                    return Flux.just(ServerSentEvent.<String>builder().event("error").data(ERROR_DATA).build());
                });
    }

    /** FastAPI GET /api/v1/portfolio 중계. 5xx · 연결 거부 · 타임아웃은 503, 4xx 는 그대로 전파한다. */
    public Mono<List<StockQuote>> portfolio() {
        return webClient.get()
                .uri("/api/v1/portfolio")
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<List<StockQuote>>() {})
                .timeout(timeout)
                .onErrorMap(AiGatewayService::isFallbackTarget, e -> {
                    log.warn("포트폴리오 조회 실패: type={}, message={}", e.getClass().getSimpleName(), e.getMessage());
                    return new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,
                            "시세를 가져올 수 없습니다. 잠시 후 다시 시도해주세요.");
                });
    }

    /** 4xx(요청 자체가 잘못됨)만 fallback 대상이 아니다. 연결 거부 · 타임아웃 · 5xx · 스트림 도중 오류는 error 이벤트로 알린다. */
    static boolean isFallbackTarget(Throwable e) {
        return !(e instanceof WebClientResponseException r && r.getStatusCode().is4xxClientError());
    }
}
