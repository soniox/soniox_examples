#!/bin/bash

# Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
api_key="$SONIOX_API_KEY"
api_base="https://api.soniox.com"
file_to_transcribe="coffee_shop.mp3"

function poll_until_complete {
  transcription_id=$1
  while true; do
    res=$(curl -s -X GET "$api_base/v1/transcriptions/$transcription_id" \
      -H "Authorization: Bearer $api_key")
    if [[ ! -z "$(echo "$res" | jq -r '.error_type // empty')" ]]; then
      echo "Error getting transcription: $res"
      exit 1
    fi

    status=$(echo "$res" | jq -r '.status')

    if [[ "$status" == "completed" ]]; then
      return
    elif [[ "$status" == "error" ]]; then
      error=$(echo "$res" | jq -r '.error_message')
      echo "Transcription error: $error"
      exit 1
    fi

    # Wait for 1 second before polling again
    sleep 1
  done
}

if ! command -v curl &>/dev/null || ! command -v jq &>/dev/null; then
  echo "Error: curl and jq are required. Please install them and try again."
  exit 1
fi

echo "Starting file upload..."

res=$(curl -s -X POST "$api_base/v1/files" \
  -H "Authorization: Bearer $api_key" \
  -F "file=@$file_to_transcribe")
if [[ ! -z "$(echo "$res" | jq -r '.error_type // empty')" ]]; then
  echo "Error uploading file: $res"
  exit 1
fi

file_id=$(echo "$res" | jq -r '.id')
if [[ -z "$file_id" || "$file_id" == "null" ]]; then
  echo "Error uploading file: $res"
  exit 1
fi

echo "Starting transcription..."

res=$(curl -s -X POST "$api_base/v1/transcriptions" \
  -H "Authorization: Bearer $api_key" \
  -H "Content-Type: application/json" \
  -d "{
    \"file_id\": \"$file_id\",
    \"model\": \"stt-async-preview\",
    \"language_hints\": [\"en\", \"es\"]
  }")
if [[ ! -z "$(echo "$res" | jq -r '.error_type // empty')" ]]; then
  echo "Error creating transcription: $res"
  exit 1
fi
transcription_id=$(echo "$res" | jq -r '.id')
if [[ "$transcription_id" == "null" ]]; then
  echo "Error creating transcription: $res"
  exit 1
fi

echo "Transcription ID: $transcription_id"

poll_until_complete $transcription_id

# Get the transcript text
res=$(curl -s -X GET "$api_base/v1/transcriptions/$transcription_id/transcript" \
  -H "Authorization: Bearer $api_key")
if [[ ! -z "$(echo "$res" | jq -r '.error_type // empty')" ]]; then
  echo "Error retrieving transcript: $res"
  exit 1
fi
transcript_text=$(echo "$res" | jq -r '.text')
if [[ -z "$transcript_text" || "$transcript_text" == "null" ]]; then
  echo "Error retrieving transcript: $res"
  exit 1
fi
echo "Transcript:"
echo $transcript_text

# Delete the transcription
curl -f -X DELETE "$api_base/v1/transcriptions/$transcription_id" \
  -H "Authorization: Bearer $api_key"

# Delete the file
curl -f -X DELETE "$api_base/v1/files/$file_id" \
  -H "Authorization: Bearer $api_key"
