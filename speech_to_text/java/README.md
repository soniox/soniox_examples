# Java examples

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

Async examples require Java 8 or newer, real-time examples require Java 11 or
newer.

## Async (REST API)

### Transcribe a file from URL

```sh
cd async/remote_file
mvn compile
mvn exec:java
```

### Transcribe a local file

```sh
cd async/local_file
mvn compile
mvn exec:java
```

## Real-time (WebSocket API)

### Stream a local file

```sh
cd real_time/stream_file
mvn compile
mvn exec:java
```

## Run with Docker

You can also run the examples with Docker:

```sh
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/examples -w /examples \
    docker.io/eclipse-temurin:11.0.25_9-jdk bash -c \
    'wget -q -P /tmp https://dlcdn.apache.org/maven/maven-3/3.9.9/binaries/apache-maven-3.9.9-bin.tar.gz &&
    tar -C /tmp -xf /tmp/apache-maven-3.9.9-bin.tar.gz 2>/dev/null;
    export PATH=/tmp/apache-maven-3.9.9/bin:$PATH &&
    exec bash'
```
