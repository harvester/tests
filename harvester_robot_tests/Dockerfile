FROM python:3.11-slim

LABEL maintainer="Harvester Team"
LABEL description="Harvester Robot Framework E2E Test Suite"

# Set working directory
WORKDIR /harvester-robot-tests

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Install kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && chmod +x kubectl \
    && mv kubectl /usr/local/bin/

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy test framework
COPY . .

# Set Python path
ENV PYTHONPATH=/harvester-robot-tests/libs

# Create output directory
RUN mkdir -p /tmp/harvester-test-report

# Set permissions
RUN chmod +x run.sh

# Default command
CMD ["./run.sh"]
