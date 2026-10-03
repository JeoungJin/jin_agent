package com.jin.gateway;

import static org.assertj.core.api.Assertions.assertThat;

import com.jin.gateway.dto.AiRouteRequest;
import com.jin.gateway.service.AiGatewayService;
import java.time.Duration;
import java.util.concurrent.TimeUnit;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import okhttp3.mockwebserver.RecordedRequest;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.test.StepVerifier;

/** MockWebServer를 가짜 FastAPI로 세워서 Service만 단독 검증한다. */
class AiGatewayServiceTest {

    static final com.jin.gateway.security.AuthUser USER = new com.jin.gateway.security.AuthUser(7L, "u@b.com");
    static final String TOKEN = "tok.en.value";

    MockWebServer fastApi;
    AiGatewayService service;

    @BeforeEach
    void setUp() throws Exception {
        fastApi = new MockWebServer();
        fastApi.start();
        service = new AiGatewayService(WebClient.create(fastApi.url("/").toString()), Duration.ofSeconds(1));
    }

    @AfterEach
    void tearDown() throws Exception {
        fastApi.shutdown();
    }

    @Test
    void 정상응답은_Mono로_그대로_전달된다() throws Exception {
        fastApi.enqueue(new MockResponse().setHeader("Content-Type", "application/json")
                .setBody("{\"question\":\"삼성전자 주가\",\"answer\":\"71,000원\",\"category\":\"stock\",\"extra\":1}"));

        StepVerifier.create(service.route(new AiRouteRequest("삼성전자 주가"), USER, TOKEN))
                .assertNext(r -> {
                    assertThat(r.answer()).isEqualTo("71,000원");
                    assertThat(r.category()).isEqualTo("stock");
                })
                .verifyComplete();

        RecordedRequest sent = fastApi.takeRequest();
        assertThat(sent.getMethod()).isEqualTo("POST");
        assertThat(sent.getPath()).isEqualTo("/api/v1/route");
        assertThat(sent.getBody().readUtf8()).isEqualTo("{\"question\":\"삼성전자 주가\",\"user_id\":7}");
        assertThat(sent.getHeader("Authorization")).isEqualTo("Bearer tok.en.value");
    }

    @Test
    void 서버오류_500이면_fallback() {
        fastApi.enqueue(new MockResponse().setResponseCode(500));

        StepVerifier.create(service.route(new AiRouteRequest("잔액"), USER, TOKEN))
                .assertNext(r -> {
                    assertThat(r.category()).isEqualTo("FALLBACK");
                    assertThat(r.question()).isEqualTo("잔액");
                })
                .verifyComplete();
    }

    @Test
    void 연결_실패면_fallback() throws Exception {
        fastApi.shutdown();

        StepVerifier.create(service.route(new AiRouteRequest("잔액"), USER, TOKEN))
                .assertNext(r -> assertThat(r.category()).isEqualTo("FALLBACK"))
                .verifyComplete();
    }

    @Test
    void 응답이_타임아웃을_넘기면_fallback() {
        fastApi.enqueue(new MockResponse().setHeader("Content-Type", "application/json")
                .setBody("{\"question\":\"q\",\"answer\":\"late\",\"category\":\"general\"}")
                .setBodyDelay(3, TimeUnit.SECONDS));

        StepVerifier.create(service.route(new AiRouteRequest("q"), USER, TOKEN))
                .assertNext(r -> assertThat(r.category()).isEqualTo("FALLBACK"))
                .verifyComplete();
    }

    @Test
    void FastAPI_4xx는_fallback하지_않고_에러로_전파된다() {
        fastApi.enqueue(new MockResponse().setResponseCode(422).setHeader("Content-Type", "application/json").setBody("{\"detail\":[]}"));

        StepVerifier.create(service.route(new AiRouteRequest("q"), USER, TOKEN))
                .expectErrorSatisfies(e -> assertThat(e).isInstanceOf(
                        org.springframework.web.reactive.function.client.WebClientResponseException.UnprocessableEntity.class))
                .verify();
    }
}
