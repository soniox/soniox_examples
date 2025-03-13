# Python examples

## Setup

```sh
export SONIOX_API_KEY=<your_soniox_api_key>
```

## Run examples

### Transcribe file from URL

```sh
cd transcribe_file/remote
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 remote.py
```

or run with Docker

```sh
cd transcribe_file/remote
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    docker.io/alpine sh -c \
    'apk add -q py3-pip &&
    python3 -m venv .venv &&
    source .venv/bin/activate &&
    pip install -r requirements.txt &&
    python3 remote.py'
```

### Transcribe local file

```sh
cd transcribe_file/local
wget https://soniox.com/media/examples/coffee_shop.mp3
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 local.py
```

or run with Docker

```sh
cd transcribe_file/local
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

**Transcription with language hints:**

```sh
cd transcribe_file/language_hints
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 language_hints.py
```

or run with Docker

```sh
cd transcribe_file/language_hints
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    docker.io/alpine sh -c \
    'apk add -q py3-pip &&
    python3 -m venv .venv &&
    source .venv/bin/activate &&
    pip install -r requirements.txt &&
    python3 language_hints.py'
```

**Transcription with speaker tags enabled:**

```sh
cd transcribe_file/speaker_tags
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 speaker_tags.py
```

or run with Docker

```sh
cd transcribe_file/speaker_tags
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    docker.io/alpine sh -c \
    'apk add -q py3-pip &&
    python3 -m venv .venv &&
    source .venv/bin/activate &&
    pip install -r requirements.txt &&
    python3 speaker_tags.py'
```

**Transcription with context:**

```sh
cd transcribe_file/context
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 context.py
```

or run with Docker

```sh
cd transcribe_file/context
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    docker.io/alpine sh -c \
    'apk add -q py3-pip &&
    python3 -m venv .venv &&
    source .venv/bin/activate &&
    pip install -r requirements.txt &&
    python3 context.py'
```

### Real-time transcription over WebSocket

```sh
cd real_time_transcription/realtime
wget https://soniox.com/media/examples/coffee_shop.pcm_s16le
# ffmpeg -i coffee_shop.mp3 -f s16le -ar 16000 -ac 1 coffee_shop.pcm_s16le
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 realtime.py
```

or run with Docker

```sh
cd real_time_transcription/realtime
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
    python3 realtime.py'
```
