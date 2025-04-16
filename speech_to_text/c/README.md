# C examples

## Download example files

```sh
# For async transcriptions
wget https://soniox.com/media/examples/coffee_shop.mp3

# Raw audio for real time transcriptions
wget https://soniox.com/media/examples/coffee_shop.pcm_s16le
# You can use ffmpeg to convert your file into PCM format
# ffmpeg -i coffee_shop.mp3 -f s16le -ar 16000 -ac 1 coffee_shop.pcm_s16le
```

## Setup

```sh
export SONIOX_API_KEY=<your_soniox_api_key>
```

Install `[libcurl](https://curl.se/libcurl/)`,
`[json-c](https://github.com/json-c/json-c)` and
`[libwebsockets](https://github.com/warmcat/libwebsockets)`.

## Async (REST API)

### Transcribe a file from URL

```sh
make async_remote_file
./async_remote_file
```

### Transcribe a local file

```sh
make async_local_file
./async_local_file
```

## Real-time (WebSocket API)

### Stream a local file

```sh
make real_time_stream_file
./real_time_stream_file
```

## Run with Docker

You can also run the examples with Docker:

```sh
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/examples -w /examples \
    docker.io/alpine sh -c \
    'apk add -q make gcc libc-dev curl-dev json-c-dev libwebsockets-dev &&
    exec sh'
```
