package main

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"time"

	"github.com/gorilla/websocket"
)

type StartRequest struct {
	ApiKey        string   `json:"api_key"`
	Model         string   `json:"model"`
	AudioFormat   string   `json:"audio_format,omitempty"`
	SampleRate    int      `json:"sample_rate,omitempty"`
	NumChannels   int      `json:"num_channels,omitempty"`
}

type Token struct {
	Text       string  `json:"text"`
	StartMs    int     `json:"start_ms"`
	EndMs      int     `json:"end_ms"`
	Confidence float32 `json:"confidence"`
}

type Response struct {
	Text         string  `json:"text"`
	Tokens       []Token `json:"tokens"`
	Finished     bool    `json:"finished,omitempty"`
	ErrorCode    int     `json:"error_code,omitempty"`
	ErrorMessage string  `json:"error_message,omitempty"`
}

func main() {
	apiKey := os.Getenv("SONIOX_API_KEY")

	file, err := os.Open("coffee_shop.pcm_s16le")
	if err != nil {
		panic(err)
	}

	// Connect to WebSocket API

	fmt.Println("Opening WebSocket connection...")

	conn, _, err := websocket.DefaultDialer.Dial(
		"wss://stt-rt.soniox.com/transcribe-websocket",
		nil,
	)
	if err != nil {
		panic(err)
	}
	defer conn.Close()

	// Send start request

	startRequest, err := json.Marshal(StartRequest{
		ApiKey:        apiKey,
		AudioFormat:   "pcm_s16le",
		SampleRate:    16000,
		NumChannels:   1,
		Model:         "stt-rt-preview"
	})
	if err != nil {
		panic(err)
	}

	if err := conn.WriteMessage(websocket.TextMessage, startRequest); err != nil {
		panic(err)
	}

	// Start send audio goroutine

	sendAudioDone := make(chan error, 1)

	go func() {
		sendAudioDone <- func() error {
			// Send audio data

			buffer := make([]byte, 3840)

			for {
				n, err := file.Read(buffer)
				if err != nil && err != io.EOF {
					return err
				}
				if n == 0 {
					break
				}

				if err := conn.WriteMessage(websocket.BinaryMessage, buffer[:n]); err != nil {
					return err
				}

				// Sleep for 120 ms
				time.Sleep(120 * time.Millisecond)
			}

			// Send end of file

			if err := conn.WriteMessage(websocket.TextMessage, []byte{}); err != nil {
				return err
			}

			return nil
		}()
	}()

	fmt.Println("Transcription started.")

	// Receive text

	for {
		_, message, err := conn.ReadMessage()
		if err != nil {
			if websocket.IsCloseError(err, websocket.CloseNormalClosure) {
				text := err.(*websocket.CloseError).Text
				if text != "" {
					fmt.Printf("Close error: %s\n", text)
				}
				break
			}

			panic(err)
		}

		var res Response
		if err := json.Unmarshal(message, &res); err != nil {
			panic(err)
		}

		if res.ErrorCode != 0 {
			fmt.Printf("\nError: %d %s\n", res.ErrorCode, res.ErrorMessage)
			break
		}

		for _, token := range res.Tokens {
			fmt.Print(token.Text)
			_ = os.Stdout.Sync()
		}

		if res.Finished {
			fmt.Println("\nTranscription done.")
		}
	}

	if err := <-sendAudioDone; err != nil {
		panic(err)
	}
}
