package com.jin.gateway;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.asyncDispatch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;

import jakarta.servlet.http.Cookie;
import java.nio.charset.StandardCharsets;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

/** 3일차 4-2: GET /api/ai/portfolio 프록시 (정상 / 5xx → 503 / 4xx 전파 / 인증 401) */
@SpringBootTest(properties = "ai.fastapi.timeout=1s")
@AutoConfigureMockMvc
class PortfolioProxyTest {

    static MockWebServer fastApi = new MockWebServer();

    static {
        try { fastApi.start(); } catch (Exception e) { throw new RuntimeException(e); }
    }

    @DynamicPropertySource
    static void props(DynamicPropertyRegistry r) {
        r.add("fastapi.base-url", () -> fastApi.url("/").toString());
    }

    @AfterAll
    static void stop() throws Exception { fastApi.shutdown(); }

    @Autowired MockMvc mvc;
    Cookie cookie;

    @BeforeEach
    void login() throws Exception {
        cookie = mvc.perform(post("/api/auth/login").contentType(MediaType.APPLICATION_JSON)
                .content("{\"email\":\"t@b.com\"}")).andReturn().getResponse().getCookie("access_token");
    }

    private MvcResult call(Cookie c) throws Exception {
        var req = get("/api/ai/portfolio");
        if (c != null) req = req.cookie(c);
        MvcResult started = mvc.perform(req).andReturn();
        if (started.getRequest().isAsyncStarted()) {
            started.getAsyncResult(5000);
            return mvc.perform(asyncDispatch(started)).andReturn();
        }
        return started;
    }

    @Test
    void 정상이면_FastAPI_목록을_그대로_준다() throws Exception {
        fastApi.enqueue(new MockResponse().setHeader("Content-Type", "application/json")
                .setBody("[{\"ticker\":\"005930.KS\",\"name\":\"삼성전자\",\"price\":71000,\"changePercent\":1.43}]"));
        MvcResult r = call(cookie);
        assertThat(r.getResponse().getStatus()).isEqualTo(200);
        assertThat(r.getResponse().getContentAsString(StandardCharsets.UTF_8))
                .contains("\"ticker\":\"005930.KS\"", "\"name\":\"삼성전자\"", "\"price\":71000", "\"changePercent\":1.43");
    }

    @Test
    void FastAPI_5xx는_503_안내_메시지() throws Exception {
        fastApi.enqueue(new MockResponse().setResponseCode(503));
        MvcResult r = call(cookie);
        assertThat(r.getResponse().getStatus()).isEqualTo(503);
        assertThat(r.getResponse().getContentAsString(StandardCharsets.UTF_8))
                .contains("\"status\":503", "시세를 가져올 수 없습니다. 잠시 후 다시 시도해주세요.");
    }

    @Test
    void FastAPI_4xx는_상태코드_그대로() throws Exception {
        fastApi.enqueue(new MockResponse().setResponseCode(404));
        assertThat(call(cookie).getResponse().getStatus()).isEqualTo(404);
    }

    @Test
    void 타임아웃이면_503() throws Exception {
        fastApi.enqueue(new MockResponse().setHeadersDelay(3, java.util.concurrent.TimeUnit.SECONDS)
                .setBody("[]"));
        assertThat(call(cookie).getResponse().getStatus()).isEqualTo(503);
    }

    @Test
    void 쿠키가_없으면_401() throws Exception {
        assertThat(call(null).getResponse().getStatus()).isEqualTo(401);
    }
}
