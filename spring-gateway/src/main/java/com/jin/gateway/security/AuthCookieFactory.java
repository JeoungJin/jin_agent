package com.jin.gateway.security;

import java.time.Duration;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseCookie;
import org.springframework.stereotype.Component;

/** 토큰을 담는 HttpOnly 쿠키(발급용)와 삭제용 쿠키를 만든다. */
@Component
public class AuthCookieFactory {

    private final String cookieName;
    private final boolean secure;
    private final long expirationMs;

    public AuthCookieFactory(@Value("${jwt.cookie-name}") String cookieName,
                             @Value("${jwt.cookie-secure}") boolean secure,
                             @Value("${jwt.expiration-ms}") long expirationMs) {
        this.cookieName = cookieName;
        this.secure = secure;
        this.expirationMs = expirationMs;
    }

    public String cookieName() {
        return cookieName;
    }

    public ResponseCookie create(String token) {
        return base(token).maxAge(Duration.ofMillis(expirationMs)).build();
    }

    /** 같은 속성에 Max-Age=0 이어야 브라우저가 쿠키를 지운다. */
    public ResponseCookie delete() {
        return base("").maxAge(Duration.ZERO).build();
    }

    private ResponseCookie.ResponseCookieBuilder base(String value) {
        return ResponseCookie.from(cookieName, value)
                .httpOnly(true)
                .secure(secure)
                .sameSite("Lax")
                .path("/");
    }
}
