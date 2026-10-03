package com.jin.gateway;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.asyncDispatch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import com.jin.gateway.controller.AiRouteController;
import com.jin.gateway.dto.AiRouteResponse;
import com.jin.gateway.service.AiGatewayService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import reactor.core.publisher.Mono;

@WebMvcTest(AiRouteController.class)
class AiRouteControllerTest {

    @Autowired MockMvc mvc;
    @MockitoBean AiGatewayService service;

    @Test
    void Mono_응답을_JSON으로_내려준다() throws Exception {
        when(service.route(any())).thenReturn(Mono.just(new AiRouteResponse("질문", "답변", "general")));

        var started = mvc.perform(post("/api/ai/route").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"question\":\"질문\"}"))
                .andExpect(request().asyncStarted())
                .andReturn();

        mvc.perform(asyncDispatch(started))
                .andExpect(status().isOk())
                .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.question").value("질문"))
                .andExpect(jsonPath("$.answer").value("답변"))
                .andExpect(jsonPath("$.category").value("general"));
    }

    @Test
    void 빈_질문은_400이고_서비스는_호출되지_않는다() throws Exception {
        mvc.perform(post("/api/ai/route").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"question\":\"\"}"))
                .andExpect(status().isBadRequest());
        verifyNoInteractions(service);
    }
}
