package com.jin.gateway.controller;

import com.jin.gateway.dto.AiRouteRequest;
import com.jin.gateway.dto.AiRouteResponse;
import com.jin.gateway.security.AuthUser;
import com.jin.gateway.service.AiGatewayService;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.GetMapping;
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

    private static final Logger log = LoggerFactory.getLogger(AiRouteController.class);

    private final AiGatewayService gatewayService;

    public AiRouteController(AiGatewayService gatewayService) {
        this.gatewayService = gatewayService;
    }

    @PostMapping("/route")
    public Mono<AiRouteResponse> route(@AuthenticationPrincipal AuthUser user, @Valid @RequestBody AiRouteRequest request) {
        log.info("AI 질문: userId={}, question='{}'", user == null ? null : user.id(), request.question());
        // Mono 는 다른 스레드에서 실행되므로 SecurityContext 를 쓸 수 없다. 지금(요청 스레드)에서 토큰 원문을 꺼내 넘긴다.
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        String accessToken = authentication == null ? null : (String) authentication.getCredentials();
        return gatewayService.route(request, user, accessToken);
    }

    /** 프론트가 로그인 여부 확인에 사용: 200이면 로그인 상태, 401이면 로그아웃 상태 */
    @GetMapping("/me")
    public AuthUser me() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        return (AuthUser) authentication.getPrincipal();
    }
}
