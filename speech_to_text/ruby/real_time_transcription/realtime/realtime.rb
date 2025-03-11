require 'json'
require 'websocket-client-simple'

websocket_url = 'wss://stt-rt.soniox.com/transcribe-websocket'
file_to_stream = 'coffee_shop.pcm_s16le'

# Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
api_key = ENV['SONIOX_API_KEY']

# Connect to WebSocket API
puts 'Opening WebSocket connection...'
ws = WebSocket::Client::Simple.connect(websocket_url)

send_audio_thread = nil

ws.on :open do
  # Send start request
  ws.send({
    'api_key' => api_key,
    'audio_format' => 'pcm_s16le',
    'sample_rate' => 16000,
    'num_channels' => 1,
    'model' => 'stt-rt-preview',
    'language_hints' => []
  }.to_json)

  # Start a thread to send audio
  send_audio_thread = Thread.new do
    # Read and send audio data from file over WebSocket connection
    File.open(file_to_stream, 'rb') do |file|
      loop do
        data = file.read(3840)
        break if data.nil?

        ws.send(data, type: :binary)
        # Sleep for 120 ms
        sleep 0.12
      end
    end

    # Signal end of file
    ws.send('')
  end
  puts 'Transcription started.'
end

ws.on :message do |msg|
  if msg.type == :text
    # Receive text
    response = JSON.parse(msg.data)

    if response['error_code']
      puts "\nError: #{response['error_code']} #{response['error_message']}"
      exit 1
    end

    if response['tokens']
      response['tokens'].each do |token|
        print token['text'] if token['text']
      end
    end

    if response['finished']
      puts "\nTranscription done."
      ws.close
    end
  end
end

ws.on :error do |e|
  # handle WebSocket connection errors
  STDERR.puts "Error: #{e.message}"
end

ws.thread.join

send_audio_thread.join unless send_audio_thread.nil?
