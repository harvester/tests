# Setting Up Default Dockerfile For Backend E2E Tests For CI
FROM python:3.10.20-bookworm@sha256:a5f03e7129c31f5d68ea83a6c2f65ffadd049be17ef4df5901aefb41a609de6f
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential findutils wget && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
# Set WORKDIR to this dir, then copy content
WORKDIR /
# Copy all content
COPY . .
# Install dependencies
RUN pip install --no-cache-dir -r test-requirements.txt
