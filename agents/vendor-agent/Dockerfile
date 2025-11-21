FROM python:3.10-slim

WORKDIR /app

# Install ffmpeg for Whisper audio processing
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

# --- Copy requirements using correct path ---
COPY agents/vendor-agent/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt
# Install Python Whisper
RUN pip install --no-cache-dir openai-whisper

# --- Copy shared folder from root context ---
COPY shared /app/shared

# --- Copy vendor-agent code ---
COPY agents/vendor-agent /app

ENV PYTHONPATH=/app

CMD ["python", "app.py"]
