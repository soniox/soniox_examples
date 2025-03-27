# Transcribe local file using Python

## Setup

```sh
export SONIOX_API_KEY=<your_soniox_api_key>
```

## Run example

```sh
wget https://soniox.com/media/examples/coffee_shop.mp3
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 local.py
```

or run with Docker

```sh
wget https://soniox.com/media/examples/coffee_shop.mp3
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    docker.io/alpine sh -c \
    'apk add -q py3-pip &&
    python3 -m venv .venv &&
    source .venv/bin/activate &&
    pip install -r requirements.txt &&
    python3 local.py'
```
