# Go examples

## Setup

```sh
export SONIOX_API_KEY=<your_soniox_api_key>
```

## Run examples

### Transcribe file from URL

```sh
cd transcribe_file/remote
go run .
```

or run with Docker

```sh
cd transcribe_file/remote
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    docker.io/golang:1.23-alpine sh -c \
    'go run .'
```

### Transcribe local file

```sh
cd transcribe_file/local
wget https://soniox.com/media/examples/coffee_shop.mp3
go run .
```

or run with Docker

```sh
cd transcribe_file/local
wget https://soniox.com/media/examples/coffee_shop.mp3
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    docker.io/golang:1.23-alpine sh -c \
    'go run .'
```

### Real-time transcription over WebSocket

```sh
cd real_time_transcription/realtime
wget https://soniox.com/media/examples/coffee_shop.pcm_s16le
# ffmpeg -i coffee_shop.mp3 -f s16le -ar 16000 -ac 1 coffee_shop.pcm_s16le
go run .
```

or run with Docker

```sh
cd real_time_transcription/realtime
wget https://soniox.com/media/examples/coffee_shop.pcm_s16le
# ffmpeg -i coffee_shop.mp3 -f s16le -ar 16000 -ac 1 coffee_shop.pcm_s16le
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    docker.io/golang:1.23-alpine sh -c \
    'go run .'
```
