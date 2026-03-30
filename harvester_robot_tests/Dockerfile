# https://apps.rancher.io/artifacts/6b458a91fc2c37c904bce4a9cd888f8d5f6d91bfb1b7fc9395ad52de1d639db7
FROM dp.apps.rancher.io/containers/kubectl@sha256:6b458a91fc2c37c904bce4a9cd888f8d5f6d91bfb1b7fc9395ad52de1d639db7 AS kubectl-binary-1-35-3

FROM python:3.11.15-slim@sha256:9358444059ed78e2975ada2c189f1c1a3144a5dab6f35bff8c981afb38946634
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
COPY --from=kubectl-binary-1-35-3 /usr/bin/kubectl /usr/local/bin/kubectl
RUN chmod +x /usr/local/bin/kubectl

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
