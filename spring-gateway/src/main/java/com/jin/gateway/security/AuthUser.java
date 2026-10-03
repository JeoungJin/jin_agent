package com.jin.gateway.security;

/** 로그인한 사용자. 토큰에 담기고, 요청마다 SecurityContext 에 복원된다. */
public record AuthUser(Long id, String email) {
}
