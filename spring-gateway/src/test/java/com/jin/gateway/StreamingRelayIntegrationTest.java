package com.jin.gateway;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.asyncDispatch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import jakarta.servlet.http.Cookie;
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

/** 3일차 Step2 [7. 확인]: 정상 순서 / FastAPI 중지·5xx → error / FastAPI 4xx → 같은 상태코드 / 빈 질문 400 / 인증 401 */
@SpringBootTest(properties = "ai.fastapi.timeout=1s")
@AutoConfigureMockMvc
class StreamingRelayIntegrationTest {

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

    private MvcResult streamed(String json) throws Exception {
        MvcResult started = mvc.perform(post("/api/ai/route").cookie(cookie).contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.TEXT_EVENT_STREAM).content(json)).andReturn();
        if (started.getRequest().isAsyncStarted()) {
            started.getAsyncResult(5000);
            return mvc.perform(asyncDispatch(started)).andReturn();
        }
        return started;
    }

    @Test
    void 정상_이벤트가_순서대로_text_event_stream_으로_나간다() throws Exception {
        fastApi.enqueue(new MockResponse().setHeader("Content-Type", "text/event-stream")
                .setBody(AiGatewayServiceTest.SSE_BODY));

        MvcResult r = streamed("{\"question\":\"q\"}");
        String body = r.getResponse().getContentAsString(java.nio.charset.StandardCharsets.UTF_8);

        assertThat(r.getResponse().getStatus()).isEqualTo(200);
        assertThat(r.getResponse().getContentType()).startsWith("text/event-stream");
        assertThat(r.getResponse().getHeader("Cache-Control")).isEqualTo("no-cache");
        assertThat(r.getResponse().getHeader("X-Accel-Buffering")).isEqualTo("no");
        assertThat(body.indexOf("event:category")).isLessThan(body.indexOf("event:token"));
        assertThat(body.indexOf("event:token")).isLessThan(body.indexOf("event:done"));
        assertThat(body).contains("{\"text\":\"안녕\"}");
    }

    @Test
    void FastAPI_5xx는_error_이벤트() throws Exception {
        fastApi.enqueue(new MockResponse().setResponseCode(503));
        String body = streamed("{\"question\":\"q\"}").getResponse().getContentAsString(java.nio.charset.StandardCharsets.UTF_8);
        assertThat(body).contains("event:error").contains("현재 AI 서비스가 원활하지 않습니다").doesNotContain("event:done");
    }

    @Test
    void FastAPI_4xx는_fallback_없이_같은_상태코드() throws Exception {
        fastApi.enqueue(new MockResponse().setResponseCode(422).setHeader("Content-Type", "application/json").setBody("{\"detail\":[]}"));
        MvcResult r = streamed("{\"question\":\"q\"}");
        assertThat(r.getResponse().getStatus()).isEqualTo(422);
        assertThat(r.getResponse().getContentAsString(java.nio.charset.StandardCharsets.UTF_8)).contains("\"status\":422");
    }

    @Test
    void 빈_질문은_FastAPI를_호출하지_않고_JSON_400() throws Exception {
        int before = fastApi.getRequestCount();
        for (String body : new String[]{"{\"question\":\"\"}", "{\"question\":\"  \"}", "{}"}) {
            MvcResult r = streamed(body);
            assertThat(r.getResponse().getStatus()).isEqualTo(400);
            assertThat(r.getResponse().getContentAsString(java.nio.charset.StandardCharsets.UTF_8)).contains("\"message\":\"질문을 입력해주세요\"");
        }
        assertThat(fastApi.getRequestCount()).isEqualTo(before);
    }

    @Test
    void 쿠키_없으면_401() throws Exception {
        mvc.perform(post("/api/ai/route").contentType(MediaType.APPLICATION_JSON).content("{\"question\":\"q\"}"))
                .andExpect(status().isUnauthorized());
    }
}
