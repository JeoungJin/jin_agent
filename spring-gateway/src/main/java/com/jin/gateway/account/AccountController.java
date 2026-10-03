package com.jin.gateway.account;

import com.jin.gateway.security.AuthUser;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

/**
 * 내부 API: FastAPI 의 계좌조회 Tool 이 서버 간 호출하는 API. (외부 사용자용이 아니다)
 * 테스트용 인메모리 잔액을 돌려주고, 토큰의 사용자와 요청한 userId 가 다르면 403 으로 막는다.
 * ※ 운영에서는 /internal/** 을 게이트웨이/네트워크 단에서 외부에 노출하지 않아야 한다.
 */
@RestController
public class AccountController {

    public record BalanceResponse(Long userId, long balance) {
    }

    private static final Map<Long, Long> BALANCES = Map.of(
            1L, 3_250_000L,
            2L, 480_000L);

    @GetMapping("/internal/api/accounts/{userId}/balance")
    public BalanceResponse balance(@PathVariable Long userId, @AuthenticationPrincipal AuthUser user) {
        // 인가 먼저: 남의 계좌는 존재 여부도 알려주지 않는다
        if (user == null || !user.id().equals(userId)) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "본인의 계좌만 조회할 수 있습니다");
        }
        Long balance = BALANCES.get(userId);
        if (balance == null) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "계좌를 찾을 수 없습니다");
        }
        return new BalanceResponse(userId, balance);
    }
}
