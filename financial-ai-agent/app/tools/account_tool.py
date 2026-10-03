"""ACCOUNT 질문용 Tool: SpringBoot 내부 API 로 계좌 잔액을 조회한다.

계좌 잔액은 우리 은행 DB(SpringBoot)에 있는 데이터라서 FastAPI 가 직접 갖지 않고 내부 API 를 호출한다.
규칙: 어떤 경우에도 예외를 밖으로 던지지 않고, 사용자에게 보여줄 한국어 문자열을 반환한다.
"""
from typing import Optional

import httpx

from app import config

MSG_INVALID_USER = "올바른 사용자 ID가 아닙니다. 로그인 후 다시 시도해주세요."
MSG_CONNECT = "계좌 서비스에 연결할 수 없습니다. 잠시 후 다시 시도해주세요."
MSG_TIMEOUT = "계좌 서비스 응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요."
MSG_NOT_FOUND = "해당 사용자의 계좌를 찾을 수 없습니다."
MSG_UNAUTHORIZED = "로그인이 필요합니다. 다시 로그인해주세요."
MSG_FORBIDDEN = "해당 계좌를 조회할 권한이 없습니다."
MSG_SERVER = "계좌 서비스에 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
MSG_UNKNOWN = "계좌 조회 중 오류가 발생했습니다."

_STATUS_MESSAGES = {404: MSG_NOT_FOUND, 401: MSG_UNAUTHORIZED, 403: MSG_FORBIDDEN}


def get_account_balance(user_id, access_token: Optional[str] = None, *, client: Optional[httpx.Client] = None) -> str:
    # 호출 전 검증: 숫자(양의 정수)가 아니면 요청을 보내지 않는다 (경로에 이상한 값이 들어가는 것도 막는다)
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
        return MSG_INVALID_USER

    url = f"{config.SPRING_API_BASE_URL}/internal/api/accounts/{user_id}/balance"
    headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}
    owns_client = client is None
    http = client or httpx.Client(timeout=config.SPRING_API_TIMEOUT)
    try:
        response = http.get(url, headers=headers)
        if response.status_code == 200:
            return f"현재 계좌 잔액은 {int(response.json()['balance']):,}원입니다."
        if response.status_code in _STATUS_MESSAGES:
            return _STATUS_MESSAGES[response.status_code]
        if response.status_code >= 500:
            return MSG_SERVER
        return MSG_UNKNOWN
    except httpx.ConnectError:
        return MSG_CONNECT
    except httpx.TimeoutException:
        return MSG_TIMEOUT
    except Exception:  # JSON 형식 오류 등 예상 못한 모든 경우
        return MSG_UNKNOWN
    finally:
        if owns_client:
            http.close()
