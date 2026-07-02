FROM registry.suse.com/bci/python:3.10

LABEL maintainer="Harvester Team"
LABEL description="Harvester Robot Framework E2E Test Suite"

ARG ARCH=amd64
ENV ARCH=${ARCH}

# Set working directory
WORKDIR /harvester-robot-tests

RUN zypper rm -y container-suseconnect && \
    zypper --no-gpg-checks ref && \
    zypper in -y git curl openssh-clients iputils vim && zypper clean -a

ARG KUBECTL_VERSION=v1.35.5
ARG KUBECTL_SHA256_amd64=90f75ea6ecc9ea5633262e1c0b83a40560003b30fc94a04cb099404fcef0c224
ARG KUBECTL_SHA256_arm64=ac69e06fd6860d69786692f5af1c3a1208ed54f8366a4d97ab15c172e99765ee

RUN KUBECTL_SHA256=KUBECTL_SHA256_${ARCH} && \
    curl -sfL https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${ARCH}/kubectl > /usr/bin/kubectl && \
    echo "${!KUBECTL_SHA256}  /usr/bin/kubectl" | sha256sum -c - && \
    chmod +x /usr/bin/kubectl

RUN --mount=from=dir_apiclient,target=/tmp/apiclient cp -r /tmp/apiclient /

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

# hack to avoid permission denied error when running pabot in container
RUN touch .pabotsuitenames && chmod 666 .pabotsuitenames

# Default command
ENTRYPOINT ["./run.sh"]
