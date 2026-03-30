# 5.4.0 version overall with chart
# version mc client , mc:0.20250813.083541-8.4
# sha256:4d82b0fc31c9f59ae5b6c3b3ae0a37396d711e33468c5c89b25bf6c1da269f83
FROM dp.apps.rancher.io/containers/mc@sha256:4d82b0fc31c9f59ae5b6c3b3ae0a37396d711e33468c5c89b25bf6c1da269f83 AS rancher-minio-client-binary-source
FROM cypress/base:16@sha256:f4d5f616e83ee6f37913ea18bc1bc4f483bd49b3d7353d04a555af034087b9ff

RUN apt-get update
RUN apt-get install -y git

COPY --from=rancher-minio-client-binary-source /usr/bin/mc /usr/local/bin/mc
# Validate the downloaded binary and abort the build if the checksum doesn't match
RUN chmod +x /usr/local/bin/mc

RUN git clone https://github.com/harvester/tests.git

WORKDIR /tests/cypress

COPY . /tests/cypress

RUN npm install

ENV PATH /tests/cypress/node_modules/.bin:$PATH

CMD ["./scripts/e2e"]
