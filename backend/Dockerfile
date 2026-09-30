FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && groupadd --gid 10001 sigeflot \
    && useradd --uid 10001 --gid sigeflot --create-home --shell /usr/sbin/nologin sigeflot

COPY --chown=sigeflot:sigeflot app ./app
COPY --chown=sigeflot:sigeflot migrations ./migrations
COPY --chown=sigeflot:sigeflot alembic.ini ./alembic.ini

RUN mkdir -p /app/.data/documentos \
    && chown -R sigeflot:sigeflot /app/.data

USER sigeflot

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
