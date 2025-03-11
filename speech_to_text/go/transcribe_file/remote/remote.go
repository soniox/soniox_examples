package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"
)

func main() {
	apiBase := "https://api.soniox.com"
	apiKey := os.Getenv("SONIOX_API_KEY")
	audioUrl := "https://soniox.com/media/examples/coffee_shop.mp3"

	// 1. Start a new transcription session by sending the audio URL to the API
	fmt.Println("Starting transcription...")
	transcriptionPayload := map[string]string{
		"audio_url": audioUrl,
		"model":     "stt-async-preview",
	}
	transcriptionBody, err := json.Marshal(transcriptionPayload)
	if err != nil {
		log.Fatalf("Failed to marshal request payload: %v", err)
	}

	req, err := http.NewRequest("POST", fmt.Sprintf("%s/v1/transcriptions", apiBase), bytes.NewReader(transcriptionBody))
	if err != nil {
		log.Fatalf("Failed to create request: %v", err)
	}
	req.Header.Set("Authorization", "Bearer "+apiKey)
	req.Header.Set("Content-Type", "application/json")

	res, err := http.DefaultClient.Do(req)
	if err != nil {
		log.Fatalf("Request failed: %v", err)
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusCreated {
		log.Fatalf("Request failed with status: %s", res.Status)
	}

	var transcription map[string]interface{}
	if err := json.NewDecoder(res.Body).Decode(&transcription); err != nil {
		log.Fatalf("Failed to decode response: %v", err)
	}

	transcriptionID, ok := transcription["id"].(string)
	if !ok {
		log.Fatalf("Failed to get transcription ID from response")
	}
	fmt.Println("Transcription started with ID: " + transcriptionID)

	// 2. Poll the transcription endpoint until the status is 'completed'
	for {
		req, err := http.NewRequest("GET", fmt.Sprintf("%s/v1/transcriptions/%s", apiBase, transcriptionID), nil)
		if err != nil {
			log.Fatalf("Failed to create request: %v", err)
		}
		req.Header.Set("Authorization", "Bearer "+apiKey)

		res, err := http.DefaultClient.Do(req)
		if err != nil {
			log.Fatalf("Request failed: %v", err)
		}
		defer res.Body.Close()

		if res.StatusCode != http.StatusOK {
			log.Fatalf("Request failed with status: %s", res.Status)
		}

		var statusResponse map[string]interface{}
		if err := json.NewDecoder(res.Body).Decode(&statusResponse); err != nil {
			log.Fatalf("Failed to decode response: %v", err)
		}

		if status, ok := statusResponse["status"].(string); ok {
			if status == "error" {
				errorMessage, _ := statusResponse["error_message"].(string)
				log.Fatalf("Transcription error: %s", errorMessage)
			} else if status == "completed" {
				break
			}
		}

		// Wait for 1 second before polling again
		time.Sleep(1 * time.Second)
	}

	// 3. Retrieve the final transcript once transcription is completed
	req, err = http.NewRequest("GET", fmt.Sprintf("%s/v1/transcriptions/%s/transcript", apiBase, transcriptionID), nil)
	if err != nil {
		log.Fatalf("Failed to create request: %v", err)
	}
	req.Header.Set("Authorization", "Bearer "+apiKey)

	res, err = http.DefaultClient.Do(req)
	if err != nil {
		log.Fatalf("Request failed: %v", err)
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		log.Fatalf("Request failed with status: %s", res.Status)
	}

	var transcriptResponse map[string]interface{}
	if err := json.NewDecoder(res.Body).Decode(&transcriptResponse); err != nil {
		log.Fatalf("Failed to decode response: %v", err)
	}

	transcriptText, ok := transcriptResponse["text"].(string)
	if !ok {
		log.Fatalf("Failed to get transcript text from response")
	}

	fmt.Printf("Transcript:\n%s\n", transcriptText)
}
