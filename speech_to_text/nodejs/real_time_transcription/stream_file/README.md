# Stream a local file using Node.js

This example shows how to live stream a file by sending it in data chunks to Soniox Speech-to-Text Real-time API and get transcribed text back.

## Setup

```sh
export SONIOX_API_KEY=<your_soniox_api_key>
```

## Run

```sh
wget https://soniox.com/media/examples/coffee_shop.pcm_s16le
# ffmpeg -i coffee_shop.mp3 -f s16le -ar 16000 -ac 1 coffee_shop.pcm_s16le
npm install
node stream_file.js
```

or run with Docker

```sh
wget https://soniox.com/media/examples/coffee_shop.pcm_s16le
# ffmpeg -i coffee_shop.mp3 -f s16le -ar 16000 -ac 1 coffee_shop.pcm_s16le
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    docker.io/node:22-alpine3.19 sh -c \
    'npm install && node stream_file.js'
```
