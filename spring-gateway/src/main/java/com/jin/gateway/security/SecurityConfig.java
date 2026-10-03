package com.jin.gateway.security;

import jakarta.servlet.DispatcherType;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpStatus;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.HttpStatusEntryPoint;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

@Configuration
public class SecurityConfig {

    /** 로그인 없이 접근 가능한 URL */
    static final String[] PUBLIC_URLS = {
            "/api/auth/login", "/api/auth/logout", "/api/auth/signup",
            "/v3/api-docs/**", "/swagger-ui/**", "/swagger-ui.html",
            "/error"
    };

    @Bean
    SecurityFilterChain filterChain(HttpSecurity http, JwtTokenProvider tokenProvider,
                                    @Value("${jwt.cookie-name}") String cookieName) throws Exception {
        http
                .csrf(AbstractHttpConfigurer::disable)          // 쿠키 인증이지만 SameSite=Lax + JSON 요청으로 방어
                .formLogin(AbstractHttpConfigurer::disable)
                .httpBasic(AbstractHttpConfigurer::disable)
                .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .exceptionHandling(e -> e.authenticationEntryPoint(new HttpStatusEntryPoint(HttpStatus.UNAUTHORIZED)))
                .authorizeHttpRequests(auth -> auth
                        // Mono/Flux 를 반환하면 MVC 는 응답을 비동기로 처리하고, 결과를 쓸 때 ASYNC 재디스패치가 일어난다.
                        // 이때 인증을 다시 검사하면 이미 처리된 요청이 401 로 덮어써진다. (최초 요청에서 이미 인증했다)
                        .dispatcherTypeMatchers(DispatcherType.ASYNC, DispatcherType.ERROR).permitAll()
                        .requestMatchers(PUBLIC_URLS).permitAll()
                        .requestMatchers("/api/ai/**").authenticated()
                        .anyRequest().authenticated())
                .addFilterBefore(new JwtAuthenticationFilter(tokenProvider, cookieName),
                        UsernamePasswordAuthenticationFilter.class);
        return http.build();
    }
}
