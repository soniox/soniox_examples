require 'net/http'
require 'json'
require 'uri'
require 'openssl'

# Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
api_key = ENV["SONIOX_API_KEY"]
api_base = "https://api.soniox.com"
file_to_transcribe = "coffee_shop.mp3"

http = Net::HTTP
headers = {
  "Authorization" => "Bearer #{api_key}"
}

def poll_until_complete(http, api_base, headers, transcription_id)
  loop do
    uri = URI("#{api_base}/v1/transcriptions/#{transcription_id}")
    req = Net::HTTP::Get.new(uri, headers)
    res = http.start(uri.hostname, uri.port, use_ssl: true) do |http|
      http.request(req)
    end
    raise "Failed to get transcription: #{res.body}" unless res.is_a?(Net::HTTPSuccess)
    transcription = JSON.parse(res.body)
    case transcription["status"]
    when "completed"
      return
    when "error"
      raise "Transcription error: #{transcription["error_message"]}"
    else
      sleep 1
    end
  end
end

puts "Starting file upload..."

uri = URI("#{api_base}/v1/files")
req = Net::HTTP::Post.new(uri, headers)
req.set_form([
    ["file", File.open(file_to_transcribe, "rb")]
], "multipart/form-data")
res = http.start(uri.hostname, uri.port, use_ssl: true) do |http|
  http.request(req)
end
raise "Failed to upload file: #{res.body}" unless res.is_a?(Net::HTTPSuccess)
file_id = JSON.parse(res.body)["id"]

puts "Starting transcription..."

uri = URI("#{api_base}/v1/transcriptions")
req = Net::HTTP::Post.new(uri, headers)
req.body = {
  "file_id" => file_id,
  "model" => "stt-async-preview",
  "language_hints" => ["en", "es"]
}.to_json
req["Content-Type"] = "application/json"
res = http.start(uri.hostname, uri.port, use_ssl: true) do |http|
  http.request(req)
end
raise "Failed to create transcription: #{res.body}" unless res.is_a?(Net::HTTPSuccess)
transcription_id = JSON.parse(res.body)["id"]
puts "Transcription ID: #{transcription_id}"

poll_until_complete(http, api_base, headers, transcription_id)

# Get the transcript text
uri = URI("#{api_base}/v1/transcriptions/#{transcription_id}/transcript")
req = Net::HTTP::Get.new(uri, headers)
res = http.start(uri.hostname, uri.port, use_ssl: true) do |http|
  http.request(req)
end
raise "Failed to get transcript: #{res.body}" unless res.is_a?(Net::HTTPSuccess)
transcript = JSON.parse(res.body)
puts "Transcript:"
puts "#{transcript["text"]}"

# Delete the transcription
uri = URI("#{api_base}/v1/transcriptions/#{transcription_id}")
req = Net::HTTP::Delete.new(uri, headers)
res = http.start(uri.hostname, uri.port, use_ssl: true) do |http|
  http.request(req)
end
raise "Failed to delete transcription: #{res.body}" unless res.is_a?(Net::HTTPSuccess)

# Delete the file
uri = URI("#{api_base}/v1/files/#{file_id}")
req = Net::HTTP::Delete.new(uri, headers)
res = http.start(uri.hostname, uri.port, use_ssl: true) do |http|
  http.request(req)
end
raise "Failed to delete file: #{res.body}" unless res.is_a?(Net::HTTPSuccess)
