FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY src/ ./src/

ENV AGENT_LLM_BASE_URL=https://api.openai.com/v1
ENV AGENT_JAVA_BASE_URL=http://app:8080

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
