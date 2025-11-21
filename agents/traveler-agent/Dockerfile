FROM python:3.10-slim

WORKDIR /app

# Install ffmpeg for Whisper audio processing
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

# --- Copy requirements using correct path ---
COPY agents/traveler-agent/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# --- Copy shared folder ---
COPY shared /app/shared

# --- Copy traveler-agent code ---
COPY agents/traveler-agent /app

ENV PYTHONPATH=/app

CMD ["python", "app.py"]
