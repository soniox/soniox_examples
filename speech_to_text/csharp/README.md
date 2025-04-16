# C# examples

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

## Async (REST API)

### Transcribe a file from URL

```sh
cd async/remote_file
dotnet run
```

### Transcribe a local file

```sh
cd async/local_file
dotnet run
```

## Real-time (WebSocket API)

### Stream a local file

```sh
cd real_time/stream_file
dotnet run
```

## Run with Docker

You can also run the examples with Docker:

```sh
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/examples -w /examples \
    mcr.microsoft.com/dotnet/sdk:8.0
```
