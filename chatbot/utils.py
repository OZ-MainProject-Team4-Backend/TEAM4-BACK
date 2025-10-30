import os

from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam

client = OpenAI(api_key=os.getenv("GPT_API_KEY"))


def ask_gpt(prompt: str) -> str:
    from typing import List

    messages: List[ChatCompletionMessageParam] = [  # type: ignore[assignment]
        {"role": "system", "content": "너는 날씨 기반 패션 코디 추천 봇이야."},
        {"role": "user", "content": prompt},
    ]

    response: ChatCompletion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=1.0,
    )

    return response.choices[0].message.content.strip()
