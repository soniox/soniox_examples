require 'net/http'
require 'json'
require 'uri'
require 'openssl'

api_base = "https://api.soniox.com"
file_to_transcribe = "coffee_shop.mp3"

# Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
api_key = ENV["SONIOX_API_KEY"]

# Create a requests session and set the Authorization header
http = Net::HTTP
uri = URI(api_base)
headers = {
  "Authorization" => "Bearer #{api_key}"
}

# 1. Upload a file
puts "Starting file upload..."
uri = URI("#{api_base}/v1/files")
req = Net::HTTP::Post.new(uri, headers)
req.set_form([
    ["file", File.open(file_to_transcribe, "rb")]
], "multipart/form-data")

res = http.start(uri.hostname, uri.port, use_ssl: true) do |http|
  http.request(req)
end

raise "File upload failed: #{res.body}" unless res.is_a?(Net::HTTPSuccess)

file = JSON.parse(res.body)

# 2. Start a new transcription session by sending the audio URL to the API
puts "Starting transcription..."
uri = URI("#{api_base}/v1/transcriptions")
req = Net::HTTP::Post.new(uri, headers)
req.body = {
  "file_id" => file["id"],
  "model"=> "stt-async-preview"
}.to_json
req["Content-Type"] = "application/json"

res = http.start(uri.hostname, uri.port, use_ssl: true) do |http|
  http.request(req)
end

raise "Transcription request failed: #{res.body}" unless res.is_a?(Net::HTTPSuccess)

transcription = JSON.parse(res.body)

transcription_id = transcription["id"]
puts "Transcription started with ID: #{transcription_id}"

# 3. Poll the transcription endpoint until the status is 'completed'
loop do
  uri = URI("#{api_base}/v1/transcriptions/#{transcription["id"]}")
  req = Net::HTTP::Get.new(uri, headers)

  res = http.start(uri.hostname, uri.port, use_ssl: true) do |http|
    http.request(req)
  end

  raise "Transcription status check failed: #{res.body}" unless res.is_a?(Net::HTTPSuccess)

  transcription = JSON.parse(res.body)

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

# 4. Retrieve the final transcript once transcription is completed
uri = URI("#{api_base}/v1/transcriptions/#{transcription["id"]}/transcript")
req = Net::HTTP::Get.new(uri, headers)

res = http.start(uri.hostname, uri.port, use_ssl: true) do |http|
  http.request(req)
end

raise "Transcript fetch failed: #{res.body}" unless res.is_a?(Net::HTTPSuccess)

transcript = JSON.parse(res.body)

puts "Transcript:"
puts "#{transcript["text"]}"
