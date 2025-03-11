# Bash examples

## Setup

```sh
export SONIOX_API_KEY=<your_soniox_api_key>
```

## Run examples

### Transcribe file from URL

You need to install `curl` and `jq`.

```sh
cd transcribe_file/remote
./remote.sh
```

#### Run with Docker

```sh
cd transcribe_file/remote
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    docker.io/alpine sh -c \
    'apk add -q bash curl jq && ./remote.sh'
```

### Transcribe local file

You need to install `curl` and `jq`.

```sh
cd transcribe_file/local
wget https://soniox.com/media/examples/coffee_shop.mp3
./local.sh
```

#### Run with Docker

```sh
cd transcribe_file/local
wget https://soniox.com/media/examples/coffee_shop.mp3
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    docker.io/alpine sh -c \
    'apk add -q bash curl jq && ./local.sh'
```

### Real-time transcription over WebSocket

You need to install [`websocat`](https://github.com/vi/websocat) (tested with v1.13.0) and `jq`.

```sh
cd real_time_transcription/realtime
wget https://soniox.com/media/examples/coffee_shop.pcm_s16le
# ffmpeg -i coffee_shop.mp3 -f s16le -ar 16000 -ac 1 coffee_shop.pcm_s16le
./realtime.sh
```

#### Run with Docker

```sh
cd real_time_transcription/realtime
wget https://soniox.com/media/examples/coffee_shop.pcm_s16le
# ffmpeg -i coffee_shop.mp3 -f s16le -ar 16000 -ac 1 coffee_shop.pcm_s16le
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    docker.io/alpine sh -c \
    'apk add -q bash websocat jq && echo && ./realtime.sh'
```
