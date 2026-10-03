"""금융교육용 AI Assistant - Day1 첫 Vibe Coding 버전.

터미널에서 질문을 입력하면 OpenAI API가 답변한다. (투자 매수/매도 추천은 하지 않는다)
실행:  python app.py
"""
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

SYSTEM_PROMPT = (
    "너는 금융교육 전문가다. 대상은 금융을 처음 배우는 20대 초보 투자자다.\n"
    "- 어려운 전문용어는 쉬운 말로 풀어서 설명하고, 일상적인 예시를 포함한다.\n"
    "- 특정 종목이나 상품의 매수/매도 추천은 절대 하지 않는다.\n"
    "- 모르는 정보나 실시간 정보는 추측하지 말고 모른다고 말한다."
)

EXIT_WORDS = {"exit", "quit", "q", "종료"}


def create_client() -> OpenAI:
    """환경변수(.env)의 OPENAI_API_KEY 로 클라이언트를 만든다. 키가 없으면 안내 후 종료."""
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY 가 설정되지 않았습니다. .env 파일에 키를 넣어 주세요.")
    return OpenAI()


def ask_llm(question: str, client: OpenAI) -> str:
    """질문을 OpenAI 에 보내 답변 문자열을 돌려준다."""
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content or ""


def main() -> None:
    try:
        client = create_client()
    except RuntimeError as e:
        print(e)
        sys.exit(1)

    print("금융교육 AI Assistant입니다. 종료하려면 exit 를 입력하세요.")
    while True:
        try:
            question = input("\n질문> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            break
        if question.lower() in EXIT_WORDS:
            print("종료합니다.")
            break
        if not question:
            print("질문을 입력해주세요.")
            continue
        try:
            print("\n답변>", ask_llm(question, client))
        except Exception as e:  # 네트워크/키 오류 등: 프로그램이 죽지 않게 한다
            print(f"\n답변을 가져오지 못했습니다. ({type(e).__name__})")


if __name__ == "__main__":
    main()
