# Go examples

## Setup

```sh
export SONIOX_API_KEY=<your_soniox_api_key>
```

## Download example files

```sh
# For async transcriptions
wget https://soniox.com/media/examples/coffee_shop.mp3

# Raw audio for real time transcriptions
wget https://soniox.com/media/examples/coffee_shop.pcm_s16le
# You can use ffmpeg to convert your file into PCM format
# ffmpeg -i coffee_shop.mp3 -f s16le -ar 16000 -ac 1 coffee_shop.pcm_s16le
```

## Async (REST API)

### Transcribe a file from URL

```sh
go run ./async/remote_file
```

### Transcribe a local file

```sh
go run ./async/local_file
```

## Real-time (WebSocket API)

### Stream a local file

```sh
go run ./real_time/stream_file
```

## Run with Docker

You can also run the examples with Docker:

```sh
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/examples -w /examples \
    docker.io/golang:1.23-alpine
```
