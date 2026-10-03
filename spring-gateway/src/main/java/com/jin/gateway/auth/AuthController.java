package com.jin.gateway.auth;

import com.jin.gateway.security.AuthCookieFactory;
import com.jin.gateway.security.AuthUser;
import com.jin.gateway.security.JwtTokenProvider;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** 테스트용 인증 API. 이메일만 받아 인메모리로 ID 를 부여하고, 토큰은 HttpOnly 쿠키로 내려준다. */
@RestController
@RequestMapping("/api/auth")
public class AuthController {

    public record LoginRequest(@NotBlank @Email String email) {
    }

    public record LoginResponse(Long id, String email) {
    }

    private final Map<String, Long> users = new ConcurrentHashMap<>();   // 이메일 → ID (인메모리)
    private final AtomicLong sequence = new AtomicLong(0);

    private final JwtTokenProvider tokenProvider;
    private final AuthCookieFactory cookieFactory;

    public AuthController(JwtTokenProvider tokenProvider, AuthCookieFactory cookieFactory) {
        this.tokenProvider = tokenProvider;
        this.cookieFactory = cookieFactory;
    }

    @PostMapping("/login")
    public ResponseEntity<LoginResponse> login(@Valid @RequestBody LoginRequest request) {
        Long id = users.computeIfAbsent(request.email(), e -> sequence.incrementAndGet());
        String token = tokenProvider.createToken(new AuthUser(id, request.email()));
        return ResponseEntity.ok()
                .header(HttpHeaders.SET_COOKIE, cookieFactory.create(token).toString())
                .body(new LoginResponse(id, request.email()));          // 본문에는 토큰을 담지 않는다
    }

    @PostMapping("/logout")
    public ResponseEntity<Void> logout() {
        return ResponseEntity.noContent()
                .header(HttpHeaders.SET_COOKIE, cookieFactory.delete().toString())
                .build();
    }
}
