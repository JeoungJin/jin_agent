package com.jin.gateway;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import com.jin.gateway.security.AuthUser;
import com.jin.gateway.security.JwtTokenProvider;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.HttpHeaders;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockHttpServletRequestBuilder;

/** 2일차 4-4: 내부 API — 인증 · 본인 확인(403) · 없는 계좌(404) */
@SpringBootTest
@AutoConfigureMockMvc
class AccountInternalApiTest {

    @Autowired MockMvc mvc;
    @Autowired JwtTokenProvider tokens;

    private MockHttpServletRequestBuilder balance(long userId, long tokenUserId) {
        String token = tokens.createToken(new AuthUser(tokenUserId, "u" + tokenUserId + "@b.com"));
        return get("/internal/api/accounts/" + userId + "/balance").header(HttpHeaders.AUTHORIZATION, "Bearer " + token);
    }

    @Test
    void 본인_계좌는_Bearer_헤더로_조회된다() throws Exception {
        mvc.perform(balance(1, 1)).andExpect(status().isOk())
                .andExpect(jsonPath("$.userId").value(1)).andExpect(jsonPath("$.balance").value(3250000));
    }

    @Test
    void 토큰_없으면_401() throws Exception {
        mvc.perform(get("/internal/api/accounts/1/balance")).andExpect(status().isUnauthorized());
    }

    @Test
    void 남의_userId는_403() throws Exception {
        mvc.perform(balance(1, 2)).andExpect(status().isForbidden())
                .andExpect(jsonPath("$.status").value(403));
    }

    @Test
    void 없는_계좌는_404() throws Exception {
        mvc.perform(balance(999, 999)).andExpect(status().isNotFound()).andExpect(jsonPath("$.status").value(404));
    }
}
