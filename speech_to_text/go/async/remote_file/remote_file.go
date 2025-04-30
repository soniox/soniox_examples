package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"time"
)

// Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
var apiKey = os.Getenv("SONIOX_API_KEY")
var apiBase = "https://api.soniox.com"
var audioUrl = "https://soniox.com/media/examples/coffee_shop.mp3"

func pollUntilComplete(transcriptionId string) {
	for {
		req, err := http.NewRequest("GET", fmt.Sprintf("%s/v1/transcriptions/%s", apiBase, transcriptionId), nil)
		if err != nil {
			panic(err)
		}
		req.Header.Set("Authorization", "Bearer "+apiKey)
		res, err := http.DefaultClient.Do(req)
		if err != nil {
			panic(err)
		}
		defer res.Body.Close()
		if res.StatusCode != http.StatusOK {
			panic(res.Status)
		}
		var statusResponse map[string]interface{}
		if err := json.NewDecoder(res.Body).Decode(&statusResponse); err != nil {
			panic(err)
		}
		if status, ok := statusResponse["status"].(string); ok {
			if status == "error" {
				panic("Transcription error: " + statusResponse["error_message"].(string))
			} else if status == "completed" {
				break
			}
		}
		time.Sleep(1 * time.Second)
	}
}

func main() {
	fmt.Println("Starting transcription...")

	transcriptionPayload := map[string]any{
		"audio_url":      audioUrl,
		"model":          "stt-async-preview",
		"language_hints": []string{"en", "es"},
	}
	transcriptionBody, err := json.Marshal(transcriptionPayload)
	if err != nil {
		panic(err)
	}
	req, err := http.NewRequest("POST", fmt.Sprintf("%s/v1/transcriptions", apiBase), bytes.NewReader(transcriptionBody))
	if err != nil {
		panic(err)
	}
	req.Header.Set("Authorization", "Bearer "+apiKey)
	req.Header.Set("Content-Type", "application/json")
	res, err := http.DefaultClient.Do(req)
	if err != nil {
		panic(err)
	}
	defer res.Body.Close()
	if res.StatusCode != http.StatusCreated {
		panic(res.Status)
	}
	var transcription map[string]interface{}
	if err := json.NewDecoder(res.Body).Decode(&transcription); err != nil {
		panic(err)
	}
	transcriptionId := transcription["id"].(string)

	fmt.Println("Transcription ID: " + transcriptionId)

	pollUntilComplete(transcriptionId)

	// Get the transcript text
	req, err = http.NewRequest("GET", fmt.Sprintf("%s/v1/transcriptions/%s/transcript", apiBase, transcriptionId), nil)
	if err != nil {
		panic(err)
	}
	req.Header.Set("Authorization", "Bearer "+apiKey)
	res, err = http.DefaultClient.Do(req)
	if err != nil {
		panic(err)
	}
	defer res.Body.Close()
	if res.StatusCode != http.StatusOK {
		panic(res.Status)
	}
	var transcriptResponse map[string]interface{}
	if err := json.NewDecoder(res.Body).Decode(&transcriptResponse); err != nil {
		panic(err)
	}
	fmt.Printf("Transcript:\n%s\n", transcriptResponse["text"].(string))

	// Delete the transcription
	req, err = http.NewRequest("DELETE", fmt.Sprintf("%s/v1/transcriptions/%s", apiBase, transcriptionId), nil)
	if err != nil {
		panic(err)
	}
	req.Header.Set("Authorization", "Bearer "+apiKey)
	res, err = http.DefaultClient.Do(req)
	if err != nil {
		panic(err)
	}
	defer res.Body.Close()
	if res.StatusCode != http.StatusNoContent {
		panic(res.Status)
	}
}
