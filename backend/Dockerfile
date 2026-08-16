FROM python:3.12-slim

# Evita .pyc e garante log sem buffer (importante para ver a saida do worker)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY worker ./worker

# Usuario sem privilegios
RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# A API e o worker compartilham esta imagem; o worker sobrescreve o command.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
