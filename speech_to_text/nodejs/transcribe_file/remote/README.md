# Transcribe file from URL using Node.js

## Setup

```sh
export SONIOX_API_KEY=<your_soniox_api_key>
```

## Run example

```sh
npm install
node remote.js
```

or run with Docker

```sh
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    docker.io/node:22-alpine3.19 sh -c \
    'npm install && node remote.js'
```
