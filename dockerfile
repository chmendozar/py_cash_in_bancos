
FROM python

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/logs /app/cliente /app/config /app/env /app/modulos /app/test /app/utilidades

COPY . /app/

VOLUME /app/logs

ENV LOG_LEVEL=INFO
ENV LOG_FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
ENV LOG_FILE=/app/logs/app.log
ENV PYTHONUNBUFFERED=1


CMD ["python", "main.py"]