# Node.js examples

## Setup

```sh
export SONIOX_API_KEY=<your_soniox_api_key>
```

Real-time examples require Node.js v22+ or newer.

```sh
npm install
```

## Download example files

```sh
# For async transcriptions
wget https://soniox.com/media/examples/coffee_shop.mp3

# Raw audio for real time transcriptions
wget https://soniox.com/media/examples/coffee_shop.pcm_s16le
# You can use ffmpeg to convert your file into PCM format
# ffmpeg -i coffee_shop.mp3 -f s16le -ar 16000 -ac 1 coffee_shop.pcm_s16le

# Raw audio for real time translations
wget https://soniox.com/media/examples/two_way_translation.pcm_s16le
# You can use ffmpeg to convert your file into PCM format
# ffmpeg -i two_way_translation.mp3 -f s16le -ar 16000 -ac 1 two_way_translation.pcm_s16le
```

## Async (REST API)

### Transcribe a file from URL

```sh
node async/remote_file.js
```

### Transcribe a local file

```sh
node async/local_file.js
```

## Real-time (WebSocket API)

### Stream a local file

```sh
node real_time/stream_file.js
```

### Transcribe a live radio stream

Transcribe a live radio broadcast using the Soniox Speech-to-Text WebSocket API
and receive transcribed text in real-time.

If this example does not output anything it might be that there is no speech on
the example radio stream.

```sh
node real_time/stream_radio.js
```

### Browser direct stream

See [Browser direct stream example
README](real_time/browser_direct_stream/README.md).

### Browser proxy stream

See [Browser proxy stream example
README](real_time/browser_proxy_stream/README.md).

## Run with Docker

You can also run the examples with Docker:

```sh
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/examples -w /examples \
    docker.io/node:22-alpine3.19 sh -c \
    'npm install && exec sh'
```
