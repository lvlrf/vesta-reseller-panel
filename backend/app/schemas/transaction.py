yamlversion: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    volumes:
      - ./backend:/app
      - ./uploads:/app/uploads  # برای ذخیره فایل‌ها (مثل تصاویر رسید)
    env_file:
      - ./.env
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  postgres:
    image: postgres:14
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data
    env_file:
      - ./.env
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}

volumes:
  postgres_data: