#!/bin/bash

# Verify that websocat and jq are installed
if ! command -v websocat &>/dev/null || ! command -v jq &>/dev/null; then
  echo "Error: websocat and jq are required."
  exit 1
fi

# Verify that SONIOX_API_KEY env variable is set
if [ -z "$SONIOX_API_KEY" ]; then
  echo "SONIOX_API_KEY environment variable must be set"
  exit 1
fi

WEBSOCKET_URL="wss://stt-rt.soniox.com/transcribe-websocket"
FILE_TO_STREAM="coffee_shop.pcm_s16le"

if [ ! -f "$FILE_TO_STREAM" ]; then
  echo "File $FILE_TO_STREAM does not exist"
  exit 1
fi

# Prepare FIFO
input_fifo=$(mktemp -u -t realtime_XXXXXX)
mkfifo -m 0600 "${input_fifo}"

# Define parameters (adjust as needed)
audio_format="pcm_s16le"
sample_rate=16000
num_channels=1
model="stt-rt-preview"
# corresponds to 120ms at 16kHz mono 16-bit little-endian PCM
chunk_size=3840

# Start the WebSocket receiver in the background
echo "Opening WebSocket connection..."
(
  websocat -t -E "$WEBSOCKET_URL" <$input_fifo | while read -r line; do
    error_code=$(echo "$line" | jq -r '.error_code // empty')

    if [[ -n "$error_code" ]]; then
      error_message=$(echo "$line" | jq -r '.error_message // empty')
      echo -e "\nError: $error_code $error_message"
      rm -f "${input_fifo}"
      break
    fi

    echo "$line" | jq --unbuffered -r -j '[.tokens[].text] | join("")'

    finished=$(echo "$line" | jq -r '.finished // empty')
    if [[ -n "$finished" ]]; then
        echo -e "\nTranscription done."
        break
    fi
  done
  echo
) &
websocat_pid=$!

echo "Transcription started."

{
  # Send start message as JSON string message
  jq -n --compact-output \
    --arg api_key "$SONIOX_API_KEY" \
    --arg audio_format "$audio_format" \
    --arg model "$model" \
    --argjson sample_rate $sample_rate \
    --argjson num_channels $num_channels \
    '{
      "api_key": $api_key,
      "audio_format": $audio_format,
      "sample_rate": $sample_rate,
      "num_channels": $num_channels,
      "model": $model
    }'

  # Stream audio data as base64 encoded string messages as websocat does not
  # support mixed text and binary messages.
  file_size=$(stat -c '%s' "$FILE_TO_STREAM")
  chunk_size=3840
  offset=0

  while [ $offset -lt $file_size ]; do
    if [ ! -p "$input_fifo" ]; then
      break
    fi

    dd if="$FILE_TO_STREAM" bs="$chunk_size" skip=$((offset / chunk_size)) count=1 2>/dev/null | base64 | tr -d '\n'
    echo
    # Sleep for 120 ms
    sleep 0.12
    offset=$((offset + chunk_size))
  done

  if [ -p "$input_fifo" ]; then
    # Finally, send an empty message to indicate end of stream.
    echo

    # Wait websocket receiver to complete
    wait $websocat_pid
  fi
} >"${input_fifo}"

# Cleanup
rm -f "${input_fifo}"
