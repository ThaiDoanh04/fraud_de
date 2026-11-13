FROM python:3.13-slim

# LightGBM trên Linux cần thư viện OpenMP (tương tự libomp trên Mac)
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv==0.13.8

WORKDIR /app
# cài thư viện trước, copy code sau -> sửa code thì không phải cài lại thư viện (tận dụng cache)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY serving/ serving/

ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn", "serving.app:app", "--host", "0.0.0.0", "--port", "8000"]
