import os

from openai import OpenAI

client = OpenAI(api_key=os.getenv("GPT_API_KEY"))


def ask_gpt(prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "너는 날씨 기반 패션 코디 추천 챗봇이야"},
            {"role": "user", "content": prompt},
        ],
        temperature=1.0,
    )
    return response.choices[0].message.content
