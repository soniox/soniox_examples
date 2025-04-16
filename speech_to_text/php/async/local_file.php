<?php

// Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
$api_key = getenv("SONIOX_API_KEY");
$api_base = "https://api.soniox.com";
$file_to_transcribe = "coffee_shop.mp3";

$auth_header = ["Authorization: Bearer $api_key"];

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

function poll_until_complete($api_base, $auth_header, $transcription_id) {
    while (true) {
        $session = create_curl_session("$api_base/v1/transcriptions/{$transcription_id}", $auth_header);
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
    
        // Wait for 1 second before polling again
        sleep(1);
    }
}

echo "Starting file upload...\n";

$session = create_curl_session(
    "$api_base/v1/files",
    $auth_header,
    ["file" => new CURLFile($file_to_transcribe)],
    true
);
$res = curl_exec($session);
$http_status = curl_getinfo($session, CURLINFO_HTTP_CODE);
curl_close($session);
if ($http_status !== 201) {
    die("File upload failed: $res");
}
$file_id = json_decode($res, true)["id"];

echo "Starting transcription...\n";

$session = create_curl_session(
    "$api_base/v1/transcriptions",
    array_merge($auth_header, ["Content-Type: application/json"]),
    [
        "file_id" => $file_id,
        "model" => "stt-async-preview",
        "language_hints" => array("en", "es")
    ],
    true,
    true
);
$res = curl_exec($session);
$http_status = curl_getinfo($session, CURLINFO_HTTP_CODE);
curl_close($session);
if ($http_status !== 201) {
    die("Failed to create transcription: $res");
}
$transcription_id = json_decode($res, true)["id"];

echo "Transcription ID: " . $transcription_id . "\n";

poll_until_complete($api_base, $auth_header, $transcription_id);

// Get the transcript text
$session = create_curl_session("$api_base/v1/transcriptions/{$transcription_id}/transcript", $auth_header);
$res = curl_exec($session);
$http_status = curl_getinfo($session, CURLINFO_HTTP_CODE);
curl_close($session);
if ($http_status !== 200) {
    die("Failed to get transcript: $res");
}
$transcript = json_decode($res, true);
echo "Transcript:\n" . $transcript["text"] . "\n";

?>
