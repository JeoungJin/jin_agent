package com.jin.gateway;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.asyncDispatch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import jakarta.servlet.http.Cookie;
import java.util.concurrent.TimeUnit;
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
import org.springframework.test.web.servlet.ResultActions;

/** 2일차 4-3: 문서 [5. 확인] — 정상 / 빈 질문(400) / FastAPI 5xx·지연(FALLBACK) / FastAPI 4xx(상태코드 그대로) */
@SpringBootTest(properties = "ai.fastapi.timeout=1s")
@AutoConfigureMockMvc
class FallbackIntegrationTest {

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

    /** 검증 실패처럼 컨트롤러 진입 전에 끝나는 요청 (동기) */
    private ResultActions sync(String json) throws Exception {
        return mvc.perform(post("/api/ai/route").cookie(cookie).contentType(MediaType.APPLICATION_JSON).content(json));
    }

    /** Mono 를 반환하는 요청: 비동기 시작 → 결과 디스패치까지 따라간다 */
    private ResultActions async(String json) throws Exception {
        MvcResult started = sync(json).andExpect(request().asyncStarted()).andReturn();
        return mvc.perform(asyncDispatch(started));
    }

    @Test
    void 정상_호출은_FastAPI_응답을_그대로_준다() throws Exception {
        fastApi.enqueue(new MockResponse().setHeader("Content-Type", "application/json")
                .setBody("{\"question\":\"q\",\"answer\":\"정상\",\"category\":\"STOCK\"}"));
        async("{\"question\":\"q\"}").andExpect(status().isOk()).andExpect(jsonPath("$.category").value("STOCK"));
    }

    @Test
    void 빈_질문은_FastAPI를_호출하지_않고_400() throws Exception {
        int before = fastApi.getRequestCount();
        for (String body : new String[]{"{\"question\":\"\"}", "{\"question\":\"   \"}", "{\"question\":null}", "{}"}) {
            sync(body).andExpect(status().isBadRequest())
                    .andExpect(jsonPath("$.status").value(400)).andExpect(jsonPath("$.message").value("질문을 입력해주세요"));
        }
        org.assertj.core.api.Assertions.assertThat(fastApi.getRequestCount()).isEqualTo(before);
    }

    @Test
    void FastAPI_5xx는_200_FALLBACK() throws Exception {
        fastApi.enqueue(new MockResponse().setResponseCode(503));
        async("{\"question\":\"삼성전자 주가\"}").andExpect(status().isOk())
                .andExpect(jsonPath("$.category").value("FALLBACK"))
                .andExpect(jsonPath("$.question").value("삼성전자 주가"))
                .andExpect(jsonPath("$.answer").value("현재 AI 서비스가 원활하지 않습니다. 잠시 후 다시 시도해주세요"));
    }

    @Test
    void 응답_지연은_200_FALLBACK() throws Exception {
        fastApi.enqueue(new MockResponse().setHeader("Content-Type", "application/json")
                .setBody("{\"question\":\"q\",\"answer\":\"늦은 답\",\"category\":\"GENERAL\"}").setBodyDelay(3, TimeUnit.SECONDS));
        async("{\"question\":\"q\"}").andExpect(status().isOk()).andExpect(jsonPath("$.category").value("FALLBACK"));
    }

    @Test
    void FastAPI_4xx는_같은_상태코드로_전달() throws Exception {
        fastApi.enqueue(new MockResponse().setResponseCode(422).setHeader("Content-Type", "application/json").setBody("{\"detail\":[]}"));
        async("{\"question\":\"q\"}").andExpect(status().isUnprocessableEntity())
                .andExpect(jsonPath("$.status").value(422)).andExpect(jsonPath("$.message").exists());
    }
}
