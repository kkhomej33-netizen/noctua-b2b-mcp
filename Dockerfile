FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 创建非特权运行用户以符合容器安全最佳实践
RUN useradd --create-home --shell /bin/sh mcpuser

COPY pyproject.toml README.md LICENSE server.py ./

USER mcpuser

ENTRYPOINT ["python3", "/app/server.py"]
