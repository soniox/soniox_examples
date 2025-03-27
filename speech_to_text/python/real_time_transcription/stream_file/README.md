# Stream a local file using Python

This example shows how to live stream a file by sending it in data chunks to Soniox Speech-to-Text Real-time API and get transcribed text back.

## Setup

```sh
export SONIOX_API_KEY=<your_soniox_api_key>
```

## Run

```sh
wget https://soniox.com/media/examples/coffee_shop.pcm_s16le
# ffmpeg -i coffee_shop.mp3 -f s16le -ar 16000 -ac 1 coffee_shop.pcm_s16le
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 stream_file.py
```

or run with Docker

```sh
wget https://soniox.com/media/examples/coffee_shop.pcm_s16le
# ffmpeg -i coffee_shop.mp3 -f s16le -ar 16000 -ac 1 coffee_shop.pcm_s16le
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    docker.io/alpine sh -c \
    'apk add -q py3-pip &&
    python3 -m venv .venv &&
    source .venv/bin/activate &&
    pip install -r requirements.txt &&
    python3 stream_file.py'
```
