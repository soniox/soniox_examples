# Python examples

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

## Setup

```sh
export SONIOX_API_KEY=<your_soniox_api_key>
```

Setup a virtual environment and install the dependencies.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Async (REST API)

### Transcribe a file from URL

```sh
python async/remote_file.py
```

### Transcribe a local file

```sh
python async/local_file.py
```

### Transcribe a file with context

```sh
python async/context.py
```

### Transcribe a file with speaker diarization enabled

```sh
python async/speaker_diarization.py
```

### Transcribe a file with webhooks

```sh
python async/webhooks.py
```

## Real-time (WebSocket API)

### Stream a local file

```sh
python real_time/stream_file.py
```

With speaker diarization:

```sh
python real_time/stream_file_speakers.py
```

With two-way translation:

```sh
python real_time/stream_file_two_way_translation.py
```

### Stream a file from URL

```sh
python real_time/stream_remote.py
```

### Stream a file from URL with context

```sh
python real_time/stream_remote_context.py
```

### Transcribe a live radio stream

Transcribe a live radio broadcast using the Soniox Speech-to-Text WebSocket API
and receive transcribed text in real-time.

If this example does not output anything it might be that there is no speech on
the example radio stream.

```sh
python real_time/stream_radio.py
```

With speaker diarization:

```sh
python real_time/stream_radio_speakers.py
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
    docker.io/python:3.10-alpine sh -c \
    'python3 -m venv .venv &&
    source .venv/bin/activate &&
    pip install -r requirements.txt &&
    exec sh'
```
