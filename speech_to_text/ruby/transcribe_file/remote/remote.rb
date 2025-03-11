require 'net/http'
require 'json'
require 'uri'
require 'openssl'

api_base = "https://api.soniox.com"
file_to_transcribe = "https://soniox.com/media/examples/coffee_shop.mp3"

# Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
api_key = ENV["SONIOX_API_KEY"]

# Create a requests session and set the Authorization header
http = Net::HTTP
uri = URI(api_base)
headers = {
  "Authorization" => "Bearer #{api_key}"
}

# 1. Start a new transcription session by sending the audio URL to the API
puts "Starting transcription..."
uri = URI("#{api_base}/v1/transcriptions")
request = Net::HTTP::Post.new(uri, headers)
request.body = {
  "audio_url" => file_to_transcribe,
  "model" => "stt-async-preview"
}.to_json
request["Content-Type"] = "application/json"

response = http.start(uri.hostname, uri.port, use_ssl: true) do |http|
  http.request(request)
end

raise "Transcription request failed: #{response.body}" unless response.is_a?(Net::HTTPSuccess)

transcription = JSON.parse(response.body)

transcription_id = transcription["id"]
puts "Transcription started with ID: #{transcription_id}"

# 2. Poll the transcription endpoint until the status is 'completed'
loop do
  uri = URI("#{api_base}/v1/transcriptions/#{transcription_id}")
  request = Net::HTTP::Get.new(uri, headers)

  response = http.start(uri.hostname, uri.port, use_ssl: true) do |http|
    http.request(request)
  end

  raise "Transcription status check failed: #{response.body}" unless response.is_a?(Net::HTTPSuccess)

  transcription = JSON.parse(response.body)

  case transcription["status"]
  when "error"
    raise "Transcription error: #{transcription["error_message"]}"
  when "completed"
    break
  else
    # Wait for 1 second before polling again
    sleep 1
  end
end

# 3. Retrieve the final transcript once transcription is completed
uri = URI("#{api_base}/v1/transcriptions/#{transcription_id}/transcript")
request = Net::HTTP::Get.new(uri, headers)

response = http.start(uri.hostname, uri.port, use_ssl: true) do |http|
  http.request(request)
end

raise "Transcript fetch failed: #{response.body}" unless response.is_a?(Net::HTTPSuccess)

transcript = JSON.parse(response.body)

# Print the transcript text
puts "Transcript:"
puts "#{transcript["text"]}"
