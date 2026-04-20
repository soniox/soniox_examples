FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.8.14 /uv /uvx /bin/

ADD . /app

WORKDIR /app
RUN uv sync --locked

ENV PORT=5050
EXPOSE 5050

CMD ["uv", "run", "main.py"]