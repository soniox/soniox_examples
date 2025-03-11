using System;
using System.IO;
using System.Net.WebSockets;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

class Realtime
{
    static async Task Main()
    {
        var apiKey = Environment.GetEnvironmentVariable("SONIOX_API_KEY");

        var wsUri = new Uri("wss://stt-rt.soniox.com/transcribe-websocket");

        using (ClientWebSocket ws = new ClientWebSocket())
        {
            // Connect to WebSocket API
            Console.WriteLine("Opening WebSocket connection...");
            await ws.ConnectAsync(wsUri, CancellationToken.None);

            // Send start request with correct field names
            var startMessage = Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new
            {
                api_key = apiKey,
                audio_format = "pcm_s16le",
                sample_rate = 16000,
                num_channels = 1,
                model = "stt-rt-preview",
                language_hints = Array.Empty<string>()
            }));
            await ws.SendAsync(new ArraySegment<byte>(startMessage), WebSocketMessageType.Text, true, CancellationToken.None);

            // Start send audio task
            var sendAudioTask = Task.Run(async () =>
            {
                using (FileStream fs = new FileStream("coffee_shop.pcm_s16le", FileMode.Open, FileAccess.Read))
                {
                    Console.WriteLine("Transcription started.");
                    var buffer = new byte[3840];
                    int bytesRead;
                    while ((bytesRead = await fs.ReadAsync(buffer, 0, buffer.Length)) > 0)
                    {
                        if (ws.State != WebSocketState.Open)
                        {
                            return;
                        }

                        var audioChunk = new ArraySegment<byte>(buffer, 0, bytesRead);
                        await ws.SendAsync(audioChunk, WebSocketMessageType.Binary, true, CancellationToken.None);

                        await Task.Delay(120);
                    }

                    // Send end of file (empty message)
                    await ws.SendAsync(new ArraySegment<byte>(Array.Empty<byte>()), WebSocketMessageType.Text, true, CancellationToken.None);
                }
            });

            try
            {
                // Receive text
                var buffer = new byte[8192];

                while (true)
                {
                    if (ws.State != WebSocketState.Open)
                    {
                        break;
                    }

                    var result = await ws.ReceiveAsync(new ArraySegment<byte>(buffer), CancellationToken.None);

                    if (result.MessageType == WebSocketMessageType.Close)
                    {
                        await ws.CloseAsync(WebSocketCloseStatus.NormalClosure, "", CancellationToken.None);
                        break;
                    }

                    if (result.MessageType == WebSocketMessageType.Text)
                    {
                        string message = Encoding.UTF8.GetString(buffer, 0, result.Count);
                        var res = JsonSerializer.Deserialize<JsonElement>(message);

                        // Handle any possible transcription error
                        if (res.TryGetProperty("error_code", out var errorCode))
                        {
                            res.TryGetProperty("error_message", out var errorMessage);
                            Console.WriteLine("");
                            Console.WriteLine("Error {0}: {1}", errorCode.GetInt32(), errorMessage.GetString());
                            await ws.CloseAsync(WebSocketCloseStatus.NormalClosure, "", CancellationToken.None);
                            break;
                        }

                        // Process tokens
                        if (res.TryGetProperty("tokens", out var tokens))
                        {
                            foreach (var token in tokens.EnumerateArray())
                            {
                                if (token.TryGetProperty("text", out var text))
                                {
                                    Console.Write(text.GetString());
                                    Console.Out.Flush();
                                }
                            }
                        }

                        if (res.TryGetProperty("finished", out var finished) && finished.GetBoolean())
                        {
                            // Close the WebSocket
                            Console.WriteLine("\nTranscription done.");
                            await ws.CloseAsync(WebSocketCloseStatus.NormalClosure, "", CancellationToken.None);
                            break;
                        }
                    }
                }

                Console.WriteLine();
            }
            finally
            {
                await sendAudioTask;
            }
        }
    }
}
