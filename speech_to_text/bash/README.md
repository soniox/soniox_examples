# Bash examples

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

Install `curl` and `jq` for async examples. Install
[`websocat`](https://github.com/vi/websocat) (tested with v1.13.0) and `jq` for
real-time examples.

## Async (REST API)

### Transcribe a file from URL

```sh
async/remote_file.sh
```

### Transcribe a local file

```sh
async/local_file.sh
```

## Real-time (WebSocket API)

### Stream a local file

```sh
real_time/stream_file.sh
```

## Run with Docker

You can also run the examples with Docker:

```sh
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/examples -w /examples \
    docker.io/alpine sh -c \
    'apk add -q bash curl jq websocat && exec bash'
```
