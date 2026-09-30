package com.jin.gateway;

import static org.hamcrest.Matchers.containsString;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest
@AutoConfigureMockMvc
class ChatControllerTest {

    static MockWebServer fastapi = new MockWebServer();

    static {
        try { fastapi.start(); } catch (Exception e) { throw new RuntimeException(e); }
    }

    @DynamicPropertySource
    static void props(DynamicPropertyRegistry r) {
        r.add("agent.base-url", () -> fastapi.url("/").toString());
    }

    @AfterAll
    static void stop() throws Exception { fastapi.shutdown(); }

    @Autowired MockMvc mvc;

    @Test
    void chat_프록시_응답을_그대로_전달한다() throws Exception {
        fastapi.enqueue(new MockResponse().setHeader("Content-Type", "application/json")
                .setBody("{\"session_id\":\"s1\",\"answer\":\"잔액은 100원\",\"steps\":[]}"));

        mvc.perform(post("/api/chat").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"sessionId\":\"s1\",\"message\":\"잔액\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.answer").value("잔액은 100원"));
    }

    @Test
    void FastAPI가_500이면_fallback_안내를_준다() throws Exception {
        fastapi.enqueue(new MockResponse().setResponseCode(500));

        mvc.perform(post("/api/chat").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"message\":\"잔액\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.answer").value(containsString("일시적으로")));
    }

    @Test
    void 빈_메시지는_400() throws Exception {
        mvc.perform(post("/api/chat").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"message\":\"\"}"))
                .andExpect(status().isBadRequest());
    }
}
