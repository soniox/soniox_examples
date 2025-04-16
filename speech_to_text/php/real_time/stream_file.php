<?php

require "vendor/autoload.php";

use Ratchet\Client\WebSocket;
use Ratchet\Client\Connector;
use Ratchet\RFC6455\Messaging\Frame;
use React\EventLoop\Factory;
use React\Socket\ConnectionException;
use React\Stream\ReadableResourceStream;

// Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
$api_key = getenv("SONIOX_API_KEY");
$ws_uri = "wss://stt-rt.soniox.com/transcribe-websocket";
$file_to_transcribe = "coffee_shop.pcm_s16le";

$loop = Factory::create();

$connector = new Connector($loop);

// Connect to WebSocket API
echo "Opening WebSocket connection..." . PHP_EOL;
$connector($ws_uri)->then(
    function (WebSocket $ws) use ($api_key, $loop, $file_to_transcribe) {
        // Send start request
        $ws->send(
            json_encode([
                "api_key" => $api_key,
                "audio_format" => "pcm_s16le",
                "sample_rate" => 16000,
                "num_channels" => 1,
                "model" => "stt-rt-preview",
                "language_hints" => array("en", "es")
            ])
        );

        $audio_file = fopen($file_to_transcribe, "rb");
        if (!$audio_file) {
            die("Failed to open audio file." . PHP_EOL);
        }

        echo "Transcription started." . PHP_EOL;

        // Read and send audio data from file over WebSocket connection every 120 ms
        $timer = $loop->addPeriodicTimer(0.12, function ($timer) use (
            $loop,
            $ws,
            $audio_file
        ) {
            $data = fread($audio_file, 3840);

            if (feof($audio_file) || empty($data)) {
                // Send end of file

                $ws->send("");
                $loop->cancelTimer($timer);
                return;
            }

            $ws->send(new Frame($data, true, Frame::OP_BINARY));
        });

        $final_text = "";

        $ws->on("message", function ($msg) use (&$final_text) {
            // Receive text
            $res = json_decode($msg, true);

            if (isset($res["error_code"])) {
                echo PHP_EOL . "Error: " . $res["error_code"] . " " . $res["error_message"] . PHP_EOL;
                return;
            }

            $non_final_text = "";

            foreach ($res["tokens"] as $token) {
                if (!empty($token["text"])) {
                    if ($token["is_final"]) {
                        $final_text = $final_text . $token["text"];
                    } else {
                        $non_final_text = $non_final_text . $token["text"];
                    }
                }
            }

            echo "\x1b[2J\x1b[H" . // clear the screen, move to top-left corner
                $final_text . // write final text
                "\x1b[34m" . // change text color to blue
                $non_final_text . // write non-final text
                "\x1b[39m"; // reset text color

            if (array_key_exists("finished", $res) && $res["finished"]) {
                echo PHP_EOL . "Transcription done." . PHP_EOL;
            }
        });

        $ws->on("close", function ($code = null, $reason = null) use (
            $loop,
            $timer
        ) {
            $loop->cancelTimer($timer);

            if ($reason != "") {
                echo "Close error: $code - $reason" . PHP_EOL;
            }
        });
    },
    function (ConnectionException $e) {
        echo "Could not connect: {$e->getMessage()}" . PHP_EOL;
    }
);

$loop->run();

?>
