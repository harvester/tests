FROM cypress/base:16

ADD https://dl.min.io/client/mc/release/linux-amd64/mc /usr/local/bin/mc
RUN chmod +x /usr/local/bin/mc

RUN mkdir /src
WORKDIR /src

COPY . /src

RUN yarn cache clean
RUN yarn install

ENV PATH /src/node_modules/.bin:$PATH

CMD ["./scripts/e2e"]
