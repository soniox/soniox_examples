# C# examples

Examples are tested against .NET 8.0.

## Setup

```sh
export SONIOX_API_KEY=<your_soniox_api_key>
```

## Run examples

### Transcribe file from URL

```sh
cd transcribe_file/Remote
dotnet run
```

or run with Docker

```sh
cd transcribe_file/Remote
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    mcr.microsoft.com/dotnet/sdk:8.0 sh -c \
    'dotnet run'
```

### Transcribe local file

```sh
cd transcribe_file/Local
wget https://soniox.com/media/examples/coffee_shop.mp3
dotnet run
```

or run with Docker

```sh
cd transcribe_file/Local
wget https://soniox.com/media/examples/coffee_shop.mp3
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    mcr.microsoft.com/dotnet/sdk:8.0 sh -c \
    'dotnet run'
```

### Real-time transcription over WebSocket

```sh
cd real_time_transcription/Realtime
wget https://soniox.com/media/examples/coffee_shop.pcm_s16le
# ffmpeg -i coffee_shop.mp3 -f s16le -ar 16000 -ac 1 coffee_shop.pcm_s16le
dotnet run
```

or run with Docker

```sh
cd real_time_transcription/Realtime
wget https://soniox.com/media/examples/coffee_shop.pcm_s16le
# ffmpeg -i coffee_shop.mp3 -f s16le -ar 16000 -ac 1 coffee_shop.pcm_s16le
docker run --rm -it \
    -e SONIOX_API_KEY=$SONIOX_API_KEY \
    -v `pwd`:/app -w /app \
    mcr.microsoft.com/dotnet/sdk:8.0 sh -c \
    'dotnet run'
```
