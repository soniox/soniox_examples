# C examples

## Setup

Install `[libcurl](https://curl.se/libcurl/)`,
`[json-c](https://github.com/json-c/json-c)` and
`[libwebsockets](https://github.com/warmcat/libwebsockets)`.

```sh
export SONIOX_API_KEY=<your_soniox_api_key>
```

## Run examples

### Transcribe file from URL

```sh
cd transcribe_file/remote
make
./remote
```

or run with Docker

```sh
cd transcribe_file/remote
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    docker.io/alpine sh -c \
    'apk add -q make gcc libc-dev curl-dev json-c-dev && make && ./remote'
```

### Transcribe local file

```sh
cd transcribe_file/local
wget https://soniox.com/media/examples/coffee_shop.mp3
make
./local
```

or run with Docker

```sh
cd transcribe_file/local
wget https://soniox.com/media/examples/coffee_shop.mp3
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    docker.io/alpine sh -c \
    'apk add -q make gcc libc-dev curl-dev json-c-dev && make && ./local'
```

### Real-time transcription over WebSocket

```sh
cd real_time_transcription/realtime
make
wget https://soniox.com/media/examples/coffee_shop.pcm_s16le
# ffmpeg -i coffee_shop.mp3 -f s16le -ar 16000 -ac 1 coffee_shop.pcm_s16le
./websocket
```

or run with Docker

```sh
cd real_time_transcription/realtime
wget https://soniox.com/media/examples/coffee_shop.pcm_s16le
# ffmpeg -i coffee_shop.mp3 -f s16le -ar 16000 -ac 1 coffee_shop.pcm_s16le
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    docker.io/alpine sh -c \
    'apk add -q make gcc libc-dev libwebsockets-dev json-c-dev openssl-dev && make && ./realtime'
```
