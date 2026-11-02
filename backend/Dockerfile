FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    binutils libproj-dev gdal-bin libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# The runtime Hugging Face cache is mounted as the persistent `hf_cache`
# named volume by docker-compose, outside the bind-mounted application code.
ENV HF_HOME=/root/.cache/huggingface
ENV SENTENCE_TRANSFORMERS_HOME=/root/.cache/huggingface/sentence_transformers
ENV HF_HUB_DISABLE_XET=1

COPY . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["/bin/sh", "/app/start.sh"]
