# Setting Up Default Dockerfile For Backend E2E Tests For CI
FROM python:3.10.16-bookworm
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential findutils wget && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
# Set WORKDIR to this dir, then copy content
WORKDIR /
# Copy all content
COPY . .
# Install dependencies
RUN pip install --no-cache-dir -r test-requirements.txt
