package com.jin.gateway.controller;

import com.jin.gateway.dto.AiRouteRequest;
import com.jin.gateway.dto.AiRouteResponse;
import com.jin.gateway.service.AiGatewayService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

/**
 * 역할: React가 호출하는 진입점(POST /api/ai/route).
 * 입력 검증만 하고 Service의 Mono를 그대로 반환한다. 일반 JSON이라 produces 설정은 필요 없다.
 */
@RestController
@RequestMapping("/api/ai")
public class AiRouteController {

    private final AiGatewayService gatewayService;

    public AiRouteController(AiGatewayService gatewayService) {
        this.gatewayService = gatewayService;
    }

    @PostMapping("/route")
    public Mono<AiRouteResponse> route(@Valid @RequestBody AiRouteRequest request) {
        return gatewayService.route(request);
    }
}
