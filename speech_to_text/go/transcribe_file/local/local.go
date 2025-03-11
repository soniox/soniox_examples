package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"mime/multipart"
	"net/http"
	"os"
	"time"
)

func main() {
	apiBase := "https://api.soniox.com"
	apiKey := os.Getenv("SONIOX_API_KEY")
	fileToTranscribe := "coffee_shop.mp3"

	// 1. Upload a file
	fmt.Println("Starting file upload...")
	fileBytes, err := os.ReadFile(fileToTranscribe)
	if err != nil {
		panic(err)
	}

	var fileUploadBody bytes.Buffer
	fileUploadWriter := multipart.NewWriter(&fileUploadBody)
	fileUploadWriterPart, err := fileUploadWriter.CreateFormFile("file", fileToTranscribe)
	if err != nil {
		panic(err)
	}
	fileUploadWriterPart.Write(fileBytes)
	fileUploadWriter.Close()

	req, err := http.NewRequest("POST", fmt.Sprintf("%s/v1/files", apiBase), &fileUploadBody)
	if err != nil {
		panic(err)
	}
	req.Header.Set("Authorization", "Bearer "+apiKey)
	req.Header.Set("Content-Type", fileUploadWriter.FormDataContentType())

	res, err := http.DefaultClient.Do(req)
	if err != nil {
		panic(err)
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusCreated {
		panic(res.Status)
	}

	var file map[string]interface{}
	if err := json.NewDecoder(res.Body).Decode(&file); err != nil {
		panic(err)
	}

	fileID := file["id"].(string)

	// 2. Start a new transcription session by sending the audio URL to the API
	fmt.Println("Starting transcription...")
	transcriptionPayload := map[string]string{
		"file_id": fileID,
		"model":   "stt-async-preview",
	}
	transcriptionBody, err := json.Marshal(transcriptionPayload)
	if err != nil {
		panic(err)
	}

	req, err = http.NewRequest("POST", fmt.Sprintf("%s/v1/transcriptions", apiBase), bytes.NewReader(transcriptionBody))
	if err != nil {
		panic(err)
	}
	req.Header.Set("Authorization", "Bearer "+apiKey)
	req.Header.Set("Content-Type", "application/json")

	res, err = http.DefaultClient.Do(req)
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

	transcriptionID := transcription["id"].(string)
	fmt.Println("Transcription started with ID: " + transcriptionID)

	// 3. Poll the transcription endpoint until the status is 'completed'
	for {
		req, err := http.NewRequest("GET", fmt.Sprintf("%s/v1/transcriptions/%s", apiBase, transcriptionID), nil)
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
				errorMessage := statusResponse["error_message"].(string)
				fmt.Printf("Transcription error: %s\n", errorMessage)
				return
			} else if status == "completed" {
				break
			}
		}

		// Wait for 1 second before polling again
		time.Sleep(1 * time.Second)
	}

	// 4.  Retrieve the final transcript once transcription is completed
	req, err = http.NewRequest("GET", fmt.Sprintf("%s/v1/transcriptions/%s/transcript", apiBase, transcriptionID), nil)
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
}
