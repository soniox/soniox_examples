# Java examples

## Setup

```sh
export SONIOX_API_KEY=<your_soniox_api_key>
```

## Run examples

### Transcribe file from URL

Supports Java 8+.

```sh
cd transcribe_file/remote
mvn compile
mvn exec:java
```

or run with Docker

```sh
cd transcribe_file/remote
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    docker.io/eclipse-temurin:8u432-b06-jdk bash -c \
    'wget -q -P /tmp https://dlcdn.apache.org/maven/maven-3/3.9.9/binaries/apache-maven-3.9.9-bin.tar.gz &&
    tar -C /tmp -xf /tmp/apache-maven-3.9.9-bin.tar.gz 2>/dev/null; /tmp/apache-maven-3.9.9/bin/mvn -q compile &&
    /tmp/apache-maven-3.9.9/bin/mvn -q exec:java'
```

### Transcribe local file

Supports Java 8+.

```sh
cd transcribe_file/local
wget https://soniox.com/media/examples/coffee_shop.mp3
mvn compile
mvn exec:java
```

or run with Docker

```sh
cd transcribe_file/local
wget https://soniox.com/media/examples/coffee_shop.mp3
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    docker.io/eclipse-temurin:8u432-b06-jdk bash -c \
    'wget -q -P /tmp https://dlcdn.apache.org/maven/maven-3/3.9.9/binaries/apache-maven-3.9.9-bin.tar.gz &&
    tar -C /tmp -xf /tmp/apache-maven-3.9.9-bin.tar.gz 2>/dev/null; /tmp/apache-maven-3.9.9/bin/mvn -q compile &&
    /tmp/apache-maven-3.9.9/bin/mvn -q exec:java'
```

### Real-time transcription over WebSocket

Supports Java 11+.

```sh
cd real_time_transcription/realtime
wget https://soniox.com/media/examples/coffee_shop.pcm_s16le
# ffmpeg -i coffee_shop.mp3 -f s16le -ar 16000 -ac 1 coffee_shop.pcm_s16le
mvn compile
mvn exec:java
```

or run with Docker

```sh
cd real_time_transcription/realtime
wget https://soniox.com/media/examples/coffee_shop.pcm_s16le
# ffmpeg -i coffee_shop.mp3 -f s16le -ar 16000 -ac 1 coffee_shop.pcm_s16le
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    docker.io/eclipse-temurin:11.0.25_9-jdk bash -c \
    'wget -q -P /tmp https://dlcdn.apache.org/maven/maven-3/3.9.9/binaries/apache-maven-3.9.9-bin.tar.gz &&
    tar -C /tmp -xf /tmp/apache-maven-3.9.9-bin.tar.gz 2>/dev/null; /tmp/apache-maven-3.9.9/bin/mvn -q compile &&
    /tmp/apache-maven-3.9.9/bin/mvn -q exec:java'
```
