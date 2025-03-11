<?php

$api_base = "https://api.soniox.com";
$api_key = getenv("SONIOX_API_KEY");
$file_to_transcribe = "https://soniox.com/media/examples/coffee_shop.mp3";

function create_curl_session($url, $headers = [], $post_fields = null, $is_post = false, $is_json = false) {
    $curl = curl_init();
    curl_setopt($curl, CURLOPT_URL, $url);
    curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($curl, CURLOPT_HTTPHEADER, $headers);
    if ($is_post) {
        curl_setopt($curl, CURLOPT_POST, true);
        if ($is_json) {
            curl_setopt($curl, CURLOPT_POSTFIELDS, json_encode($post_fields));
        } else {
            curl_setopt($curl, CURLOPT_POSTFIELDS, $post_fields);
        }
    }
    return $curl;
}

$auth_header = ["Authorization: Bearer $api_key"];

# 1. Start a new transcription session by sending the audio URL to the API
echo "Starting transcription...\n";
$session = create_curl_session(
    "$api_base/v1/transcriptions",
    array_merge($auth_header, ["Content-Type: application/json"]),
    ["audio_url" => $file_to_transcribe, "model" => "stt-async-preview"],
    true,
    true
);

$res = curl_exec($session);
$http_status = curl_getinfo($session, CURLINFO_HTTP_CODE);
curl_close($session);

if ($http_status !== 201) {
    die("Failed to create transcription: $res");
}

$transcription = json_decode($res, true);
echo "Transcription started with ID: " . $transcription["id"] . "\n";

# 2. Poll the transcription endpoint until the status is 'completed'
while (true) {
    $session = create_curl_session("$api_base/v1/transcriptions/{$transcription["id"]}", $auth_header);
    $res = curl_exec($session);
    $http_status = curl_getinfo($session, CURLINFO_HTTP_CODE);
    curl_close($session);

    if ($http_status !== 200) {
        die("Failed to get transcription: $res");
    }

    $transcription = json_decode($res, true);

    if ($transcription["status"] === "error") {
        die("Transcription error: {$transcription["error_message"]}");
    } else if ($transcription["status"] === "completed") {
        break;
    }

    # Wait for 1 second before polling again
    sleep(1);
}

# 3. Retrieve the final transcript once transcription is completed
$session = create_curl_session("$api_base/v1/transcriptions/{$transcription["id"]}/transcript", $auth_header);
$res = curl_exec($session);
$http_status = curl_getinfo($session, CURLINFO_HTTP_CODE);
curl_close($session);

if ($http_status !== 200) {
    die("Failed to get transcript: $res");
}

$transcript = json_decode($res, true);

echo "Transcript:\n";
echo $transcript["text"] . PHP_EOL;

?>
