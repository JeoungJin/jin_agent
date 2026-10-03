package com.jin.gateway;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.asyncDispatch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import com.jin.gateway.security.AuthUser;
import com.jin.gateway.security.JwtTokenProvider;
import com.jin.gateway.service.AiGatewayService;
import jakarta.servlet.http.Cookie;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.http.codec.ServerSentEvent;
import reactor.core.publisher.Flux;

/** 2일차 4-2: JWT(HttpOnly 쿠키) 인증 — 문서의 [7. 확인] ①~④ + 위조·만료·Bearer 대체 경로 */
@SpringBootTest
@AutoConfigureMockMvc
class JwtCookieAuthTest {

    @Autowired MockMvc mvc;
    @Autowired JwtTokenProvider tokenProvider;
    @Value("${jwt.secret}") String secret;
    @MockitoBean AiGatewayService gateway;

    private MvcResult login(String email) throws Exception {
        return mvc.perform(post("/api/auth/login").contentType(MediaType.APPLICATION_JSON)
                .content("{\"email\":\"" + email + "\"}")).andExpect(status().isOk()).andReturn();
    }

    private Cookie loginCookie(String email) throws Exception {
        return login(email).getResponse().getCookie("access_token");
    }

    @Test
    void 쿠키없이_me는_401() throws Exception {
        mvc.perform(get("/api/ai/me")).andExpect(status().isUnauthorized());
    }

    @Test
    void 로그인하면_HttpOnly_SameSite_쿠키가_내려오고_본문에_토큰은_없다() throws Exception {
        MvcResult result = login("a@b.com");
        String setCookie = result.getResponse().getHeader(HttpHeaders.SET_COOKIE);
        assertThat(setCookie).contains("access_token=").contains("HttpOnly").contains("SameSite=Lax")
                .contains("Path=/").contains("Max-Age=3600");
        String body = result.getResponse().getContentAsString(java.nio.charset.StandardCharsets.UTF_8);
        assertThat(body).contains("\"email\":\"a@b.com\"").contains("\"id\":");
        assertThat(body).doesNotContain("eyJ").doesNotContain("token");
    }

    @Test
    void 쿠키로_me와_route가_200() throws Exception {
        Cookie cookie = loginCookie("me@b.com");
        mvc.perform(get("/api/ai/me").cookie(cookie)).andExpect(status().isOk())
                .andExpect(jsonPath("$.email").value("me@b.com"));

        when(gateway.route(any(), any(), any())).thenReturn(Flux.just(
                ServerSentEvent.<String>builder().event("token").data("{\"text\":\"답변\"}").build()));
        MvcResult started = mvc.perform(post("/api/ai/route").cookie(cookie).contentType(MediaType.APPLICATION_JSON)
                .content("{\"question\":\"질문\"}")).andExpect(request().asyncStarted()).andReturn();
        started.getAsyncResult(5000);
        MvcResult done = mvc.perform(asyncDispatch(started)).andExpect(status().isOk()).andReturn();
        assertThat(done.getResponse().getContentAsString(java.nio.charset.StandardCharsets.UTF_8)).contains("event:token").contains("{\"text\":\"답변\"}");
    }

    @Test
    void route도_쿠키없으면_401이고_서비스는_호출되지_않는다() throws Exception {
        mvc.perform(post("/api/ai/route").contentType(MediaType.APPLICATION_JSON).content("{\"question\":\"질문\"}"))
                .andExpect(status().isUnauthorized());
        verifyNoInteractions(gateway);
    }

    @Test
    void 로그아웃은_삭제쿠키를_내려준다() throws Exception {
        MvcResult result = mvc.perform(post("/api/auth/logout")).andExpect(status().isNoContent()).andReturn();
        assertThat(result.getResponse().getHeader(HttpHeaders.SET_COOKIE)).contains("access_token=").contains("Max-Age=0");
    }

    @Test
    void 쿠키_대신_Bearer_헤더로도_200() throws Exception {
        String token = loginCookie("bearer@b.com").getValue();
        mvc.perform(get("/api/ai/me").header(HttpHeaders.AUTHORIZATION, "Bearer " + token))
                .andExpect(status().isOk()).andExpect(jsonPath("$.email").value("bearer@b.com"));
    }

    @Test
    void 위조된_토큰은_401() throws Exception {
        String token = loginCookie("x@b.com").getValue();
        String tampered = token.substring(0, token.length() - 3) + (token.endsWith("AAA") ? "BBB" : "AAA");
        mvc.perform(get("/api/ai/me").cookie(new Cookie("access_token", tampered))).andExpect(status().isUnauthorized());
        mvc.perform(get("/api/ai/me").cookie(new Cookie("access_token", "garbage"))).andExpect(status().isUnauthorized());
    }

    @Test
    void 만료된_토큰은_401() throws Exception {
        JwtTokenProvider expired = new JwtTokenProvider(secret, -1000);
        String token = expired.createToken(new AuthUser(1L, "old@b.com"));
        mvc.perform(get("/api/ai/me").cookie(new Cookie("access_token", token))).andExpect(status().isUnauthorized());
    }

    @Test
    void 같은_이메일은_같은_ID_다른_이메일은_다른_ID() throws Exception {
        String a1 = login("same@b.com").getResponse().getContentAsString(java.nio.charset.StandardCharsets.UTF_8);
        String a2 = login("same@b.com").getResponse().getContentAsString(java.nio.charset.StandardCharsets.UTF_8);
        String b = login("other@b.com").getResponse().getContentAsString(java.nio.charset.StandardCharsets.UTF_8);
        assertThat(a1).isEqualTo(a2).isNotEqualTo(b);
    }

    @Test
    void 이메일_형식이_아니면_로그인_400() throws Exception {
        mvc.perform(post("/api/auth/login").contentType(MediaType.APPLICATION_JSON).content("{\"email\":\"nope\"}"))
                .andExpect(status().isBadRequest());
    }
}
