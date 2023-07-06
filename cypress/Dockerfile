FROM node:16

RUN mkdir /src
WORKDIR /src

COPY . /src

RUN yarn install

ENV PATH /app/node_modules/.bin:$PATH

CMD ["yarn", "run", "e2e"]
