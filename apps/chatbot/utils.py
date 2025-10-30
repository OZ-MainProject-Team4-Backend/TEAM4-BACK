import os
from functools import lru_cache
from typing import List

from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam


@lru_cache
def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY 환경변수가 설정되어 있지 않습니다. "
            "로컬에서는 .env에, CI에서는 GitHub Secrets에 등록해야 합니다."
        )
    return OpenAI(api_key=api_key)


def ask_gpt(prompt: str) -> str:
    messages: List[ChatCompletionMessageParam] = [  # type: ignore[assignment]
        {"role": "system", "content": "너는 날씨 기반 패션 코디 추천 봇이야."},
        {"role": "user", "content": prompt},
    ]

    client = get_openai_client()
    response: ChatCompletion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=1.0,
    )

    return (response.choices[0].message.content or "").strip()
