# Transcribe local file using Node.js

## Setup

```sh
export SONIOX_API_KEY=<your_soniox_api_key>
```

## Run example

```sh
cd transcribe_file/local
wget https://soniox.com/media/examples/coffee_shop.mp3
npm install
node local.js
```

or run with Docker

```sh
cd transcribe_file/local
wget https://soniox.com/media/examples/coffee_shop.mp3
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    docker.io/node:22-alpine3.19 sh -c \
    'npm install && node local.js'
```
