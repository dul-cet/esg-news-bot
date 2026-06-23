# Multi-stage build для оптимизации размера образа
FROM python:3.11-slim as base

# Установить переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Установить системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxml2-dev \
    libxslt-dev \
    zlib1g-dev \
    git \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Создать рабочую директорию
WORKDIR /app

# ==============================================================================
# Builder stage - установка зависимостей
# ==============================================================================
FROM base as builder

# Копировать requirements.txt
COPY requirements.txt .

# Создать wheels для всех зависимостей (быстрее устанавливать позже)
RUN pip install --user --no-warn-script-location -r requirements.txt

# ==============================================================================
# Runtime stage - финальный образ
# ==============================================================================
FROM base as runtime

# Копировать установленные пакеты из builder stage
COPY --from=builder /root/.local /root/.local

# Обновить PATH для использования пакетов
ENV PATH=/root/.local/bin:$PATH

# Создать необходимые директории
RUN mkdir -p /app/data /app/logs && \
    chmod 755 /app/data /app/logs

# Копировать весь код приложения
COPY . /app/

# Создать пользователя для сека (не запускать как root)
RUN useradd -m -u 1000 newsbot && \
    chown -R newsbot:newsbot /app

# Переключиться на непривилегированного пользователя
USER newsbot

# Health check - проверить что бот живой
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('/app/data/news.db') else 1)" || exit 1

# Метаданные образа
LABEL maintainer="ESG News Bot Team" \
      version="1.0.0" \
      description="ESG News Bot - Telegram интеграция для новостей" \
      org.opencontainers.image.source="https://github.com/yourname/NewsBotESG"

# Точка входа
ENTRYPOINT ["/bin/bash", "-c"]
CMD ["python main.py"]
