FROM mcr.microsoft.com/playwright/python:v1.57.0-noble

WORKDIR /app
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir .
COPY . .
RUN mkdir -p /app/data/exports /app/data/reports
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
