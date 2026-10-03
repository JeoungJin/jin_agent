package com.jin.gateway;

import static org.assertj.core.api.Assertions.assertThat;

import com.jin.gateway.dto.AiRouteRequest;
import com.jin.gateway.security.AuthUser;
import com.jin.gateway.service.AiGatewayService;
import java.time.Duration;
import java.util.List;
import java.util.concurrent.TimeUnit;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import okhttp3.mockwebserver.RecordedRequest;
import okhttp3.mockwebserver.SocketPolicy;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Flux;
import reactor.test.StepVerifier;

/** 3일차 Step2: FastAPI 의 SSE 를 Flux 로 받아 그대로 중계 / 실패 시 error 이벤트 / 4xx 는 전파 */
class AiGatewayServiceTest {

    static final AuthUser USER = new AuthUser(7L, "u@b.com");
    static final String SSE_BODY =
            "event: category\ndata: {\"question\":\"q\",\"category\":\"GENERAL\"}\n\n"
                    + "event: token\ndata: {\"text\":\"안녕\"}\n\n"
                    + "event: token\ndata: {\"text\":\"하세요\"}\n\n"
                    + "event: done\ndata: {}\n\n";

    MockWebServer fastApi;

    @BeforeEach
    void setUp() throws Exception {
        fastApi = new MockWebServer();
        fastApi.start();
    }

    @AfterEach
    void tearDown() throws Exception {
        fastApi.shutdown();
    }

    private AiGatewayService service(Duration timeout) {
        return new AiGatewayService(WebClient.create(fastApi.url("/").toString()), timeout);
    }

    private MockResponse sse(String body) {
        return new MockResponse().setHeader("Content-Type", "text/event-stream; charset=utf-8").setBody(body);
    }

    @Test
    void 이벤트를_순서와_내용_그대로_중계하고_요청_형식도_맞다() throws Exception {
        fastApi.enqueue(sse(SSE_BODY));

        StepVerifier.create(service(Duration.ofSeconds(2)).route(new AiRouteRequest("q"), USER, "tok.en"))
                .assertNext(e -> {
                    assertThat(e.event()).isEqualTo("category");
                    assertThat(e.data()).isEqualTo("{\"question\":\"q\",\"category\":\"GENERAL\"}");
                })
                .assertNext(e -> assertThat(e.event()).isEqualTo("token"))
                .assertNext(e -> assertThat(e.data()).isEqualTo("{\"text\":\"하세요\"}"))
                .assertNext(e -> assertThat(e.event()).isEqualTo("done"))
                .verifyComplete();

        RecordedRequest sent = fastApi.takeRequest();
        assertThat(sent.getMethod()).isEqualTo("POST");
        assertThat(sent.getPath()).isEqualTo("/api/v1/route");
        assertThat(sent.getHeader("Accept")).contains("text/event-stream");
        assertThat(sent.getHeader("Authorization")).isEqualTo("Bearer tok.en");
        assertThat(sent.getBody().readUtf8()).isEqualTo("{\"question\":\"q\",\"user_id\":7}");
    }

    @Test
    void 모아서_보내지_않고_도착하는_즉시_전달한다() {
        // 본문을 천천히(20바이트/0.25초) 보낸다. 전체는 오래 걸리지만 첫 이벤트는 훨씬 먼저 나와야 한다.
        fastApi.enqueue(sse(SSE_BODY).throttleBody(20, 250, TimeUnit.MILLISECONDS));
        long start = System.nanoTime();

        Flux<ServerSentEvent<String>> flux = service(Duration.ofSeconds(5)).route(new AiRouteRequest("q"), USER, "t");
        ServerSentEvent<String> first = flux.blockFirst(Duration.ofSeconds(10));
        long firstMs = (System.nanoTime() - start) / 1_000_000;

        assertThat(first.event()).isEqualTo("category");
        // 전체 본문은 (바이트 수/20 × 250ms) 이상 걸린다
        long totalMs = (long) Math.ceil(SSE_BODY.getBytes(java.nio.charset.StandardCharsets.UTF_8).length / 20.0) * 250;
        assertThat(firstMs).isLessThan(totalMs / 2);
    }

    @Test
    void FastAPI_5xx는_error_이벤트_1개로_알리고_종료() {
        fastApi.enqueue(new MockResponse().setResponseCode(503));

        StepVerifier.create(service(Duration.ofSeconds(1)).route(new AiRouteRequest("q"), USER, "t"))
                .assertNext(e -> {
                    assertThat(e.event()).isEqualTo("error");
                    assertThat(e.data()).contains("현재 AI 서비스가 원활하지 않습니다");
                })
                .verifyComplete();                       // done 은 오지 않는다
    }

    @Test
    void 연결_거부는_error_이벤트() throws Exception {
        AiGatewayService svc = service(Duration.ofSeconds(1));
        fastApi.shutdown();

        StepVerifier.create(svc.route(new AiRouteRequest("q"), USER, "t"))
                .assertNext(e -> assertThat(e.event()).isEqualTo("error"))
                .verifyComplete();
    }

    @Test
    void 이벤트_사이_대기가_타임아웃을_넘으면_error_이벤트() {
        fastApi.enqueue(sse(SSE_BODY).setBodyDelay(3, TimeUnit.SECONDS));

        StepVerifier.create(service(Duration.ofSeconds(1)).route(new AiRouteRequest("q"), USER, "t"))
                .assertNext(e -> assertThat(e.event()).isEqualTo("error"))
                .verifyComplete();
    }

    @Test
    void 스트림_도중_끊기면_받은_이벤트_뒤에_error_이벤트() {
        fastApi.enqueue(new MockResponse().setHeader("Content-Type", "text/event-stream")
                .setBody("event: category\ndata: {\"question\":\"q\",\"category\":\"GENERAL\"}\n\n"
                        + "event: token\ndata: {\"text\":\"하나\"}\n\n".repeat(8)
                        + "event: token\ndata: {\"text\":\"안")
                .setSocketPolicy(SocketPolicy.DISCONNECT_DURING_RESPONSE_BODY));

        List<ServerSentEvent<String>> events = service(Duration.ofSeconds(2))
                .route(new AiRouteRequest("q"), USER, "t").collectList().block(Duration.ofSeconds(10));

        assertThat(events.get(0).event()).isEqualTo("category");
        assertThat(events.get(events.size() - 1).event()).isEqualTo("error");
        assertThat(events).noneMatch(e -> "done".equals(e.event()));
    }

    @Test
    void FastAPI_4xx는_fallback하지_않고_에러로_전파() {
        fastApi.enqueue(new MockResponse().setResponseCode(422).setHeader("Content-Type", "application/json").setBody("{\"detail\":[]}"));

        StepVerifier.create(service(Duration.ofSeconds(1)).route(new AiRouteRequest("q"), USER, "t"))
                .expectErrorSatisfies(e -> assertThat(e).isInstanceOf(WebClientResponseException.UnprocessableEntity.class))
                .verify();
    }
}
