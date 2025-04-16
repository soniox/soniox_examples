# Ruby examples

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

Use [Bundler](https://bundler.io/) to install `websocket-client-simple` for
real-time examples.

```sh
bundle install
```

## Async (REST API)

### Transcribe a file from URL

```sh
ruby async/remote_file.rb
```

### Transcribe a local file

```sh
ruby async/local_file.rb
```

## Real-time (WebSocket API)

### Stream a local file

```sh
ruby real_time/stream_file.rb
```

## Run with Docker

You can also run the examples with Docker:

```sh
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    docker.io/ruby:3.4-alpine sh -c \
    'bundle install && exec sh'
```
