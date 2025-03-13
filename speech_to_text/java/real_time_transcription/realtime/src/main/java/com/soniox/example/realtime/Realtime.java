package com.soniox.example.realtime;

import java.io.*;
import java.net.http.HttpClient;
import java.net.http.WebSocket;
import java.net.URI;
import java.nio.*;
import java.util.concurrent.*;

import org.json.JSONObject;

public class Realtime {
    public static void main(String[] args) {
        String apiKey = System.getenv("SONIOX_API_KEY");

        ExecutorService executor = Executors.newCachedThreadPool();

        HttpClient client = HttpClient.newBuilder().executor(executor).build();

        URI wsUri = URI.create("wss://stt-rt.soniox.com/transcribe-websocket");

        CountDownLatch latch = new CountDownLatch(1);

        // Connect to WebSocket API
        System.out.println("Opening WebSocket connection...");

        WebSocket webSocket = client.newWebSocketBuilder().buildAsync(wsUri, new WebSocket.Listener() {
            @Override
            public void onOpen(WebSocket webSocket) {
                // Send start request

                JSONObject startRequest = new JSONObject();
                startRequest.put("api_key", apiKey);
                startRequest.put("audio_format", "pcm_s16le");
                startRequest.put("sample_rate", 16000);
                startRequest.put("num_channels", 1);
                startRequest.put("model", "stt-rt-preview");

                webSocket.sendText(startRequest.toString(), true);

                // Start send audio thread

                Thread sendAudioThread = new Thread(() -> {
                    // Send audio data

                    try (InputStream inputStream = new FileInputStream("coffee_shop.pcm_s16le")) {
                        System.out.println("Transcription started.");

                        try {
                            byte[] buffer = new byte[3840];
                            int bytesRead;

                            while ((bytesRead = inputStream.read(buffer)) != -1) {
                                webSocket.sendBinary(ByteBuffer.wrap(buffer, 0, bytesRead), true).join();
                                // Sleep for 120 ms
                                TimeUnit.MILLISECONDS.sleep(120);
                            }

                            // Send send of file

                            webSocket.sendText("", true).join();
                        } catch (IOException | InterruptedException | CompletionException e) {}
                    } catch (IOException e) {
                        e.printStackTrace();
                        System.exit(1);
                    }
                });
                executor.submit(sendAudioThread);

                WebSocket.Listener.super.onOpen(webSocket);
            }

            @Override
            public CompletionStage<?> onText(WebSocket webSocket, CharSequence data, boolean last) {
                // Receive text

                JSONObject response = new JSONObject(data.toString());

                // Handle any possible transcription error
                if (response.opt("error_code") != null)
                {
                    System.out.println("\nError: " + response.getInt("error_code") + ": " + response.getString("error_message"));
                    webSocket.sendClose(WebSocket.NORMAL_CLOSURE, "");
                } else {
                    // Process tokens
                    response.getJSONArray("tokens").forEach(t -> {
                        JSONObject token = (JSONObject) t;
                        if (token.getString("text") != null) {
                            System.out.print(token.getString("text"));
                            System.out.flush();
                        }
                    });

                    if (response.opt("finished") != null && response.getBoolean("finished")) {
                        // Close the WebSocket
                        System.out.println("\nTranscription done.");
                        webSocket.sendClose(WebSocket.NORMAL_CLOSURE, "");
                    }
                }

                return WebSocket.Listener.super.onText(webSocket, data, last);
            }

            @Override
            public CompletionStage<?> onClose(WebSocket webSocket, int statusCode, String reason) {
                System.out.println("");

                if (!reason.equals("")) {
                    System.out.println("Close error: " + reason);
                }

                latch.countDown();

                return WebSocket.Listener.super.onClose(webSocket, statusCode, reason);
            }

            @Override
            public void onError(WebSocket webSocket, Throwable error) {
                System.out.println("");

                error.printStackTrace();

                latch.countDown();
            }
        }).join();

        try {
            latch.await();
        } catch (InterruptedException e) {}

        executor.shutdownNow();
    }
}
