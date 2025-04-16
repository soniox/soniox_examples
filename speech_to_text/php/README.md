# Python examples

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

Examples are runnable using PHP CLI.

Use [composer](https://getcomposer.org/download/) to install `ratchet/pawl` for
real-time examples.

```sh
php composer.phar update
```

## Async (REST API)

### Transcribe a file from URL

```sh
php async/remote_file.php
```

### Transcribe a local file

```sh
php async/local_file.php
```

## Real-time (WebSocket API)

### Stream a local file

```sh
php real_time/stream_file.php
```

## Run with Docker

You can also run the examples with Docker:

```sh
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/examples -w /examples \
    docker.io/php:8.3.14 sh -c \
    'apt update </dev/null && apt install -y unzip </dev/null &&
    php -r "copy(\"https://getcomposer.org/installer\", \"composer-setup.php\");" &&
    php composer-setup.php --quiet &&
    php composer.phar update &&
    exec bash'
```
