FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q https://storage.googleapis.com/chrome-for-testing-public/latest/linux64/chromedriver-linux64.zip \
    && unzip chromedriver-linux64.zip \
    && mv chromedriver-linux64/chromedriver /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf chromedriver-linux64.zip chromedriver-linux64

COPY backend/ ./backend/
COPY frontend/dist/ ./static/

COPY backend/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/data
VOLUME ["/app/data"]

ENV PYTHONUNBUFFERED=1
ENV SECRET_KEY=avito-scanner-pro-secret-key-change-in-production

EXPOSE 5000

CMD ["python", "-m", "backend.web_app"]