# Python examples

## Setup

```sh
export SONIOX_API_KEY=<your_soniox_api_key>
```

Examples are runnable using PHP cli.

## Run examples

### Transcribe file from URL

```sh
cd transcribe_file/remote
php remote.php
```

or run with Docker

```sh
cd transcribe_file/remote
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    docker.io/php:8.3.14 sh -c \
    'php remote.php'
```

### Transcribe local file

```sh
cd transcribe_file/local
wget https://soniox.com/media/examples/coffee_shop.mp3
php local.php
```

or run with Docker

```sh
cd transcribe_file/local
wget https://soniox.com/media/examples/coffee_shop.mp3
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    docker.io/php:8.3.14 sh -c \
    'php local.php'
```

### Real-time transcription over WebSocket

Install [composer](https://getcomposer.org/download/).

```sh
cd real_time_transcription/realtime
wget https://soniox.com/media/examples/coffee_shop.pcm_s16le
# ffmpeg -i coffee_shop.mp3 -f s16le -ar 16000 -ac 1 coffee_shop.pcm_s16le
php composer.phar update
php realtime.php
```

or run with Docker

```sh
cd real_time_transcription/realtime
wget https://soniox.com/media/examples/coffee_shop.pcm_s16le
# ffmpeg -i coffee_shop.mp3 -f s16le -ar 16000 -ac 1 coffee_shop.pcm_s16le
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    docker.io/php:8.3.14 sh -c \
    'apt update && apt install -y unzip && php -r "copy(\"https://getcomposer.org/installer\", \"composer-setup.php\");" && php composer-setup.php --quiet && php composer.phar update && php realtime.php'
```
