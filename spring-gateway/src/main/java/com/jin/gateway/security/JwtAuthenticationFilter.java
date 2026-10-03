package com.jin.gateway.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.List;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.filter.OncePerRequestFilter;

/**
 * 요청마다 토큰을 꺼내 검증하고, 성공하면 SecurityContext 에 AuthUser 를 넣는다.
 * ※ @Component 로 등록하지 않는다. (등록하면 서블릿 필터로 한 번 더 실행된다) SecurityConfig 에서 직접 만든다.
 */
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private static final String BEARER = "Bearer ";

    private final JwtTokenProvider tokenProvider;
    private final String cookieName;

    public JwtAuthenticationFilter(JwtTokenProvider tokenProvider, String cookieName) {
        this.tokenProvider = tokenProvider;
        this.cookieName = cookieName;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        String token = resolveToken(request);
        if (token != null && tokenProvider.validateToken(token)) {
            AuthUser user = tokenProvider.getAuthUser(token);
            // principal = AuthUser, credentials = 토큰 원문 (이후 FastAPI 호출 때 Bearer 로 전달)
            var authentication = new UsernamePasswordAuthenticationToken(
                    user, token, List.of(new SimpleGrantedAuthority("ROLE_USER")));
            SecurityContextHolder.getContext().setAuthentication(authentication);
        }
        chain.doFilter(request, response);
    }

    /** ① 쿠키 → ② 없으면 Authorization: Bearer (curl · Swagger 테스트용 / 서버 간 호출용) */
    String resolveToken(HttpServletRequest request) {
        Cookie[] cookies = request.getCookies();
        if (cookies != null) {
            for (Cookie cookie : cookies) {
                if (cookieName.equals(cookie.getName()) && !cookie.getValue().isBlank()) {
                    return cookie.getValue();
                }
            }
        }
        String header = request.getHeader("Authorization");
        if (header != null && header.startsWith(BEARER)) {
            return header.substring(BEARER.length()).trim();
        }
        return null;
    }
}
