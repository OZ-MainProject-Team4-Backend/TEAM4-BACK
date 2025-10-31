# 베이스 이미지
FROM python:3.12-slim

# 환경 변수
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/root/.local/bin:${PATH}"

# 기본 패키지 설치 + psycopg2 의존성 추가
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV UV_PYTHON=3.12

# 작업 디렉토리
WORKDIR /team4-aws

# 의존성 파일 복사 및 설치
COPY pyproject.toml ./
RUN uv venv && \
    . ./.venv/bin/activate && \
    uv sync --all-packages && \
    pip install --no-cache-dir django psycopg2-binary gunicorn

# 앱 코드 복사
COPY . .

# 환경 변수
ARG SECRET_KEY
ENV SECRET_KEY=${SECRET_KEY}
ENV DJANGO_SETTINGS_MODULE=apps.settings


# 포트 개방
EXPOSE 8000

# 컨테이너 시작 시 uvicorn으로 Django 실행
CMD ["uv", "run", "gunicorn", "apps.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
