FROM python:3.11-slim
WORKDIR /code
RUN apt-get update && apt-get install -y --no-install-recommends bash && rm -rf /var/lib/apt/lists/*
COPY environment/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt
