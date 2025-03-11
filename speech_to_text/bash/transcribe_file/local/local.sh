#!/bin/bash

# Check if curl and jq are installed
if ! command -v curl &> /dev/null || ! command -v jq &> /dev/null; then
  echo "Error: curl and jq are required. Please install them and try again."
  exit 1
fi

API_BASE="https://api.soniox.com"
FILE_TO_TRANSCRIBE="coffee_shop.mp3"

# 1. Upload a file
echo "Starting file upload..."
RES=$(curl -s -X POST "$API_BASE/v1/files" \
  -H "Authorization: Bearer $SONIOX_API_KEY" \
  -F "file=@$FILE_TO_TRANSCRIBE")

if [[ ! -z "$(echo "$RES" | jq -r '.error_type // empty')" ]]; then
  echo -e "Error: $(echo "$RES" | jq -r '.message // empty')"
  exit 1
fi

FILE_ID=$(echo "$RES" | jq -r '.id')

if [[ -z "$FILE_ID" || "$FILE_ID" == "null" ]]; then
  echo "Error uploading file $(echo $RES | jq -r '.message')"
  exit 1
fi

# 2. Start a new transcription session by sending the audio URL to the API
echo "Starting transcription..."
RES=$(curl -s -X POST "$API_BASE/v1/transcriptions" \
  -H "Authorization: Bearer $SONIOX_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"file_id\": \"$FILE_ID\",
    \"model\": \"stt-async-preview\"
  }")

if [[ ! -z "$(echo "$RES" | jq -r '.error_type // empty')" ]]; then
  echo -e "Error: $(echo "$RES" | jq -r '.message // empty')"
  exit 1
fi

TRANSCRIPTION_ID=$(echo "$RES" | jq -r '.id')
echo "Transcription started with ID: $TRANSCRIPTION_ID"

if [[ "$TRANSCRIPTION_ID" == "null" ]]; then
  echo "Error creating transcription: $(echo "$RES" | jq -r '.message')"
  exit 1
fi

# 3. Wait for the transcription to complete

while true; do
  RES=$(curl -s -X GET "$API_BASE/v1/transcriptions/$TRANSCRIPTION_ID" \
    -H "Authorization: Bearer $SONIOX_API_KEY")

  if [[ ! -z "$(echo "$RES" | jq -r '.error_type // empty')" ]]; then
    echo -e "Error: $(echo "$RES" | jq -r '.message // empty')"
    exit 1
  fi

  STATUS=$(echo "$RES" | jq -r '.status')

  if [[ "$STATUS" == "error" ]]; then
    ERROR_MESSAGE=$(echo "$RES" | jq -r '.error_message')
    echo "Transcription error: $ERROR_MESSAGE"
    exit 1
  elif [[ "$STATUS" == "completed" ]]; then
    break
  fi

  # Wait for 1 second before polling again
  sleep 1
done

#4. Get the transcript

RES=$(curl -s -X GET "$API_BASE/v1/transcriptions/$TRANSCRIPTION_ID/transcript" \
  -H "Authorization: Bearer $SONIOX_API_KEY")

if [[ ! -z "$(echo "$RES" | jq -r '.error_type // empty')" ]]; then
  echo -e "Error: $(echo "$RES" | jq -r '.message // empty')"
  exit 1
fi

TRANSCRIPT_TEXT=$(echo "$RES" | jq -r '.text')

if [[ -z "$TRANSCRIPT_TEXT" || "$TRANSCRIPT_TEXT" == "null" ]]; then
  echo "Error retrieving transcript: $(echo "$RES" | jq -r '.message')"
  exit 1
fi

echo "Transcript:"
echo $TRANSCRIPT_TEXT
